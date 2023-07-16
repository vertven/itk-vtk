# itk-vtk

```bash
pip install -r requirements.txt
```

# VTK Viewer

The project comes with our own VTK viewer. You can find its source code in `vtk_viewer.py.`
The viewer has some valuable controls:
- Up and Down arrows: change the slice
- Mouse wheel: zoom in and out
- Left click and drag: change contrast and brightness
The images are displayed in Sagittal view.

# Image Repositioning

The code aligns two brain scans (scan1 and scan2) recorded at various times by
utilising image registration techniques, such as the Iterative Closest Point
(ICP) algorithm. This alignment makes it easier to make relevant comparisons and
analyses, which makes it possible to trace the development and evolution of
tumours across time. Using intensity-based and deformable registration
techniques, the algorithm also conducts image repositioning by lining up the
registered scan (registered_scan2) with the reference scan (scan1). By ensuring
that the images are in a similar reference space, it is possible to compare
tumour's growth accurately and evaluate the efficacy of the treatment.

# Segmentation

In the examination of tumours, segmentation is an essential stage. The program
segments the tumour regions in scan1 and registered_scan2 using a segmentation
technique based on confidence-connected region growth. The method grows the
region based on intensity similarity standards from a user-defined seed point.
To identify the tumour sections for additional analysis, such as volume
estimation and quantitative measurements, segmentation is used.

We tried to use other filters, such as: ConnectedThresholdImageFilter,
WatershedImageFilter, NeighborhoodConnectedImageFilter etc...

For `ConnectedThresholdImageFilter` the issue that we encountered is that bones
and tumors had the same  thresholds, so we couldn't segment the tumor
without segmenting the bones.

For `WatershedImageFilter,` we couldn't segment the tumor properly.
We are curious to know if using it was a good idea in the first place.

For `NeighborhoodConnectedImageFilter` the tumor was correctly segmented,
but the issue was too much information loss.
So we decided to use `ConfidenceConnectedImageFilter` because it was the best
compromise between the different filters even if the right parameters were harder to find.

For all the filters we tried to use, we based our parameters by doing
the segmentation manually using ITK-SNAP.

# Analysis

The code then analyses the tumour regions to produce quantitative measurements.
Both scan1 and registered_scan2's segmented tumour areas' volumes are
calculated. The volume measurement allows for the monitoring of treatment
success by providing an estimate of tumour size and growth over time.
Additionally, the code overlays the segmented sections from registered_scan2
onto scan1 to visually depict the progression of the tumour regions.

# Conclusion

The offered code uses image registration, repositioning, segmentation, and
analysis techniques to segment and analyse brain tumours. For meaningful
comparisons, image registration and repositioning made sure that scans were
accurately aligned. The study offered quantitative indicators including tumour
volume and a visual representation of tumour progression, and the segmentation
technique permitted the delineation of tumour regions. These techniques aid in
the proper diagnosis, planning, and surveillance of brain tumours.
