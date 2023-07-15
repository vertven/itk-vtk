import vtk
import itk
from vtkmodules.util import numpy_support


def render(images, labels, segmentations=None):

    if len(images) != len(labels):
        raise ValueError("Number of images and labels must be the same")

    renderWindow = vtk.vtkRenderWindow()
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.Initialize()

    image_size = 1 / len(images)
    imageReslices = []
    for i, (itkImage, label) in enumerate(zip(images, labels)):
        array = itk.array_from_image(itkImage)

        # Normalize the array to range 0-255
        array = ((array - array.min()) * (1 / (array.max() - array.min()) * 255)).astype('uint8')

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

        if segmentations is not None:
            segmentation = segmentations[i]

            seg_array = itk.array_from_image(segmentation)
            seg_array = (seg_array - seg_array.min()) / (seg_array.max() - seg_array.min())

            seg_vtk = numpy_support.numpy_to_vtk(seg_array.ravel(), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
            seg_image = vtk.vtkImageData()
            seg_image.SetSpacing(itkImage.GetSpacing())
            seg_image.SetOrigin(itkImage.GetOrigin())
            seg_image.SetDimensions(*itkImage.GetLargestPossibleRegion().GetSize())
            seg_image.SetSpacing(*itkImage.GetSpacing())
            size = itkImage.GetLargestPossibleRegion().GetSize()
            seg_image.SetDimensions(size[0], size[1], size[2])
            seg_image.GetPointData().SetScalars(seg_vtk)

            # Map the segmented image to red color
            colorLookupTable = vtk.vtkLookupTable()
            colorLookupTable.SetNumberOfTableValues(2)
            colorLookupTable.SetTableValue(0, 0, 0, 0, 0)
            colorLookupTable.SetTableValue(1, 1, 0, 0, 1)
            colorLookupTable.Build()

            mapTransparency = vtk.vtkImageMapToColors()
            mapTransparency.SetLookupTable(colorLookupTable)
            mapTransparency.PassAlphaToOutputOn()
            mapTransparency.SetInputData(seg_image)
            mapTransparency.Update()

            seg_actor = vtk.vtkImageActor()
            seg_actor.GetMapper().SetInputData(mapTransparency.GetOutput())
            seg_actor.GetProperty().SetOpacity(0.5)

            renderer.AddActor(seg_actor)

        renderer.AddActor(imageActor)

        cornerAnnotation = vtk.vtkCornerAnnotation()
        cornerAnnotation.SetText(0, label)
        cornerAnnotation.GetTextProperty().SetFontSize(20)
        cornerAnnotation.GetTextProperty().SetColor(1, 1, 1)
        renderer.AddViewProp(cornerAnnotation)

        setupCamera(renderer, imageActor)

        xMin = i * image_size
        xMax = (i + 1) * image_size
        renderer.SetViewport(xMin, 0, xMax, 1)


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

    renderer.ResetCamera()
    renderer.ResetCameraClippingRange()

