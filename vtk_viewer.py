import vtk
import itk
import math

import vtk
import itk
import math

def render(images, labels):
    if len(images) != len(labels):
        raise ValueError("Number of images and labels must be the same")

    render_window = vtk.vtkRenderWindow()

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)
    render_window_interactor.Initialize()

    total_images = len(images)
    image_size = 1 / total_images

    image_reslices = []
    for i, (itk_image, label) in enumerate(zip(images, labels)):
        array = itk.array_from_image(itk_image)

        # Normalize the array to range 0-255
        array = ((array - array.min()) * (1 / (array.max() - array.min()) * 255)).astype('uint32')

        # Convert the normalized array back to an ITK image
        itk_image = itk.image_from_array(array)

        source = itk.vtk_image_from_image(itk_image)

        renderer = vtk.vtkRenderer()
        renderer.GetActiveCamera().ParallelProjectionOn()

        render_window.AddRenderer(renderer)

        reslice = vtk.vtkImageReslice()
        reslice.SetInputData(source)
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxesDirectionCosines([1, 0, 0, 0, 1, 0, 0, 0, 1])
        reslice.SetResliceAxesOrigin([0, 0, 0])
        reslice.Update()
        image_reslices.append(reslice)

        image_actor = vtk.vtkImageActor()
        image_actor.GetMapper().SetInputData(reslice.GetOutput())
        renderer.AddActor(image_actor)

        corner_annotation = vtk.vtkCornerAnnotation()
        corner_annotation.SetText(0, label)
        corner_annotation.GetTextProperty().SetFontSize(20)
        corner_annotation.GetTextProperty().SetColor(1, 1, 1)
        renderer.AddViewProp(corner_annotation)

        setup_camera(renderer, image_actor, total_images)

        x_min = i * image_size
        x_max = (i + 1) * image_size
        renderer.SetViewport(x_min, 0, x_max, 1)

    max_slice = source.GetDimensions()[2] - 1
    render_window_interactor.SetInteractorStyle(
        myInteractorStyle(render_window=render_window, max_slice=max_slice, image_reslices=image_reslices))

    render_window.Render()
    render_window_interactor.Start()



class myInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, parent=None, render_window=None, max_slice=0, image_reslices=None):
        self.AddObserver("KeyPressEvent", self.key_press_event)
        self.current_slice = 0
        self.max_slice = max_slice
        self.renderWindow = render_window
        self.imageReslices = image_reslices if image_reslices is not None else []
        self.SetInteractionModeToImage3D()

    def key_press_event(self, obj, event):
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


def setup_camera(renderer, image_actor, length):
    """Configure active camera of renderer by fitting the data"""

    camera = renderer.GetActiveCamera()

    source = image_actor.GetMapper().GetInput()

    extent = source.GetExtent()
    origin = source.GetOrigin()
    spacing = source.GetSpacing()

    xcenter = origin[0] + 0.5 * (extent[0] + extent[1]) * spacing[0]
    ycenter = origin[1] + 0.5 * (extent[2] + extent[3]) * spacing[1]
    zcenter = origin[2] + 0.5 * (extent[4] + extent[5]) * spacing[2]
    ydimension = (extent[3] - extent[2] + 1) * spacing[1]

    d = camera.GetDistance()
    scale_factor = ydimension  # Increase the scale_factor

    camera.SetParallelScale(scale_factor)
    camera.SetFocalPoint(xcenter, ycenter, zcenter)
    camera.SetPosition(xcenter, ycenter, zcenter - d)
    camera.SetViewUp(0, -1, 0)

    renderer.ResetCamera()
    renderer.ResetCameraClippingRange()
