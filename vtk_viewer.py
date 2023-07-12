import vtk
import itk

def render(images):
    """ Renders multiple itk Images with VTK """

    # Create a new render window
    renderWindow = vtk.vtkRenderWindow()

    # Create a new window interactor
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.Initialize()

    imageReslices = [] 
    for i, itkImage in enumerate(images):

        array = itk.array_from_image(itkImage)

        # Normalize the array to range 0-255
        array = ((array - array.min()) * (1 / (array.max() - array.min()) * 255)).astype('uint8')

        # Convert the normalized array back to an ITK image
        itkImage = itk.image_from_array(array)

        source = itk.vtk_image_from_image(itkImage)

        renderer = vtk.vtkRenderer()
        renderer.GetActiveCamera().ParallelProjectionOn()

        renderWindow.AddRenderer(renderer)

        reslice = vtk.vtkImageReslice()
        reslice.SetInputData(source)
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxesDirectionCosines([1, 0, 0, 0, 1, 0, 0, 0, 1]) 
        reslice.SetResliceAxesOrigin([0, 0, 0]) 
        reslice.Update()
        imageReslices.append(reslice)

        imageActor = vtk.vtkImageActor()
        imageActor.GetMapper().SetInputData(reslice.GetOutput())
        renderer.AddActor(imageActor)

        # Define the position of the renderer in the render window
        renderer.SetViewport(i / len(images), 0, (i + 1) / len(images), 1)

        setupCamera(renderer, imageActor)

    max_slice = source.GetDimensions()[2] - 1
    renderWindowInteractor.SetInteractorStyle(
        myInteractorStyle(renderWindow=renderWindow, max_slice=max_slice, imageReslices=imageReslices))

    renderWindow.Render()
    renderWindowInteractor.Start()


class myInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, parent=None, renderWindow=None, max_slice=0, imageReslices=None):
        self.AddObserver("KeyPressEvent", self.keyPressEvent)
        self.current_slice = 0
        self.max_slice = max_slice
        self.renderWindow = renderWindow
        self.imageReslices = imageReslices if imageReslices is not None else []
        self.SetInteractionModeToImage3D()

    def keyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == 'Up':
            self.next_slice()
        elif key == 'Down':
            self.previous_slice()

    def next_slice(self):
        if self.current_slice < self.max_slice:
            self.current_slice += 1
            self.update_slice()

    def previous_slice(self):
        if self.current_slice > 0:
            self.current_slice -= 1
            self.update_slice()

    def update_slice(self):
        for reslice in self.imageReslices:
            reslice.SetResliceAxesOrigin([0, 0, self.current_slice])
            reslice.Update()
        self.renderWindow.Render()


def setupCamera(renderer, imageActor):
    """Configure active camera of renderer by fitting the data"""

    camera = renderer.GetActiveCamera()
    renderer.ResetCamera()
    camera.ParallelProjectionOn()

    source = imageActor.GetMapper().GetInput()

    extent = source.GetExtent()
    origin = source.GetOrigin()
    spacing = source.GetSpacing()

    xcenter = origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0]
    ycenter = origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1]
    zcenter = origin[2] + 0.5 * (extent[4] + extent[5]) * spacing[2]
    ydimension = (extent[3] - extent[2] + 1) * spacing[1]

    d = camera.GetDistance()
    scale_factor = 0.5 * ydimension
    camera.SetParallelScale(scale_factor)
    camera.SetFocalPoint(xcenter, ycenter, zcenter)
    camera.SetPosition(xcenter, ycenter, zcenter - d)
    camera.SetViewUp(0, -1, 0)

    renderer.ResetCameraClippingRange()