"""

===========================
Read/Write streamline files
===========================

Overview
========

DIPY_ can read and write many different file formats. In this example
we give a short introduction on how to use it for loading or saving
streamlines. The new statefull tractogram class was made to reduce errors
cause by spatial transformation and complex file format convention.

Read :ref:`faq`

"""

import os

import nibabel as nib
import numpy as np
from dipy.data import get_fnames
from dipy.io.stateful_tractogram import Space, StatefulTractogram
from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.io.utils import (create_nifti_header, create_tractogram_header,
                           get_reference_info, is_header_compatible)
from dipy.tracking.streamline import select_random_set_of_streamlines
from dipy.tracking.utils import density_map

from dipy.data.fetcher import (fetch_file_formats,
                               get_file_formats)

"""
First fetch the dataset that contains 5 tractography file of 5 file formats:
- cc_m_sub.trk
- laf_m_sub.tck
- lpt_m_sub.fib
- raf_m_sub.vtk
- rpt_m_sub.dpy

And their reference anatomy, common to all 5 files:
- template0.nii.gz
"""

fetch_file_formats()
bundles_filename, ref_anat_filename = get_file_formats()
for filename in bundles_filename:
    print(os.path.basename(filename))
reference_anatomy = nib.load(ref_anat_filename)

"""
Load tractogram will support 5 file formats, functions like load_trk or
load_tck will simply be restricted to one file format

TRK files contain their own header (when writen properly), so they
technically do not need a reference. (See how below)
cc_trk = load_tractogram(bundles_filename[0], 'same')
"""

cc_sft = load_tractogram(bundles_filename[0], reference_anatomy)
print(cc_sft)
laf_sft = load_tractogram(bundles_filename[1], reference_anatomy)
raf_sft = load_tractogram(bundles_filename[3], reference_anatomy)

"""
These files contain invalid streamlines (negative values once in voxel space)
This is not considered a valid tractography file, but it is possible to load
it anyway
"""

lpt_sft = load_tractogram(bundles_filename[2], reference_anatomy,
                          bbox_valid_check=False)
rpt_sft = load_tractogram(bundles_filename[4], reference_anatomy,
                          bbox_valid_check=False)

"""
The function load_tractogram requires a reference, any of the following input
is considered valid (as long as they are in the same share space)
- Nifti filename
- Trk filename
- nib.nifti1.Nifti1Image
- nib.streamlines.trk.TrkFile
- nib.nifti1.Nifti1Header
- Trk header (dict)
- Stateful Tractogram

The reason why this parameters is required is to guarantee all informations
related to space attribute are always present.
"""

affine, dimensions, voxel_sizes, voxel_order = get_reference_info(
    reference_anatomy)
print(affine)
print(dimensions)
print(voxel_sizes)
print(voxel_order)

"""
If you have a Trk file that was generated using a particular anatomy,
to be considered valid all fields must correspond between the headers.
It can be easily verified using this function, which also accept
the same variety of input as get_reference_info
"""

print(is_header_compatible(reference_anatomy, bundles_filename[0]))

"""
If a TRK was generated with a valid header, but the reference NIFTI was lost
an header can be generated to then generate a fake NIFTI file.

If you wish to manually save Trk and Tck file using nibabel streamlines
API for more freedom of action (not recommanded for beginner) you can
create valid header using create_tractogram_header
"""

nifti_header = create_nifti_header(affine, dimensions, voxel_sizes)
nib.save(nib.Nifti1Image(np.zeros(dimensions), affine, nifti_header),
         'fake.nii.gz')
nib.save(reference_anatomy, os.path.basename(ref_anat_filename))

"""
Once loaded, no matter the original file format, the stateful tractogram is 
self contained and maintain a valid state and can be easily be manipulated
Let's save all file as TRK to visualize in TrackVis for example.
However, when loaded the lpt and rpt files contains invalid streamlines and
for particular operations/tools/functions it is safer to remove them
"""

save_tractogram(cc_sft, 'cc.trk')
save_tractogram(laf_sft, 'laf.trk')
save_tractogram(raf_sft, 'raf.trk')

print(lpt_sft.is_bbox_in_vox_valid())
lpt_sft.remove_invalid_streamlines()
print(lpt_sft.is_bbox_in_vox_valid())
save_tractogram(lpt_sft, 'lpt.trk')

print(rpt_sft.is_bbox_in_vox_valid())
rpt_sft.remove_invalid_streamlines()
print(rpt_sft.is_bbox_in_vox_valid())
save_tractogram(rpt_sft, 'rpt.trk')

"""
Some functions in dipy require streamlines to be in voxel space so computation
can be perfomed on a grid (connectivity matrix, ROIs masking, density map).
The stateful tractogram class provided safe function for such manipulation.
These function can be called safely over and over, by knowing in which state
the tractogram is the operation is computed only necessary. 

No matter the state, function such as saving or removing invalid coordinate
can be called safely and the transformation are handle internally if needed.
"""

cc_sft.to_voxmm()
print(cc_sft.space)
cc_sft.to_rasmm()
print(cc_sft.space)

"""
Now lets move them all to voxel space, subsample them to 100 streamlines,
compute a density map and save everything for visualisation in another
software such as Trackvis or MI-Brain.
"""

cc_sft.to_vox()
laf_sft.to_vox()
raf_sft.to_vox()
lpt_sft.to_vox()
rpt_sft.to_vox()

cc_streamlines_vox = select_random_set_of_streamlines(cc_sft.streamlines,
                                                      1000)
laf_streamlines_vox = select_random_set_of_streamlines(laf_sft.streamlines,
                                                       1000)
raf_streamlines_vox = select_random_set_of_streamlines(raf_sft.streamlines,
                                                       1000)
lpt_streamlines_vox = select_random_set_of_streamlines(lpt_sft.streamlines,
                                                       1000)
rpt_streamlines_vox = select_random_set_of_streamlines(rpt_sft.streamlines,
                                                       1000)

# Same dimensions for every stateful tractogram, can be re-use
affine, dimensions, voxel_sizes, voxel_order = cc_sft.space_attribute
cc_density = density_map(cc_streamlines_vox, dimensions)
laf_density = density_map(laf_streamlines_vox, dimensions)
raf_density = density_map(raf_streamlines_vox, dimensions)
lpt_density = density_map(lpt_streamlines_vox, dimensions)
rpt_density = density_map(rpt_streamlines_vox, dimensions)

"""
Replacing streamlines is possible, but if the state was modified between
operation such as this one is not recommanded:
-> cc_sft.streamlines = cc_streamlines_vox

It is recommanded to re-create a new StatefulTractogram object and
explicitely specified in which space the streamline are. Be careful to follow
the order of operations.

If the tractogram was from a Trk file with metadata, this will be lost.
If you wish to keep metadata while manipulating the number or the order
look the function StatefulTractogram.remove_invalid_streamlines() for more
details

It is important to mention that once the object is created in a consistent state
the save_tractogram function will save a valid file. And then the function 
load_tractogram will load them in a valid state.
"""

cc_sft = StatefulTractogram(cc_streamlines_vox, reference_anatomy, Space.VOX)
laf_sft = StatefulTractogram(laf_streamlines_vox, reference_anatomy, Space.VOX)
raf_sft = StatefulTractogram(raf_streamlines_vox, reference_anatomy, Space.VOX)
lpt_sft = StatefulTractogram(lpt_streamlines_vox, reference_anatomy, Space.VOX)
rpt_sft = StatefulTractogram(rpt_streamlines_vox, reference_anatomy, Space.VOX)

print(len(cc_sft), len(laf_sft), len(raf_sft), len(lpt_sft), len(rpt_sft))
save_tractogram(cc_sft, 'cc_1000.trk')
save_tractogram(laf_sft, 'laf_1000.trk')
save_tractogram(raf_sft, 'raf_1000.trk')
save_tractogram(lpt_sft, 'lpt_1000.trk')
save_tractogram(rpt_sft, 'rpt_1000.trk')

nib.save(nib.Nifti1Image(cc_density, affine, nifti_header),
         'cc_density.nii.gz')
nib.save(nib.Nifti1Image(laf_density, affine, nifti_header),
         'laf_density.nii.gz')
nib.save(nib.Nifti1Image(raf_density, affine, nifti_header),
         'raf_density.nii.gz')
nib.save(nib.Nifti1Image(lpt_density, affine, nifti_header),
         'lpt_density.nii.gz')
nib.save(nib.Nifti1Image(rpt_density, affine, nifti_header),
         'rpt_density.nii.gz')
