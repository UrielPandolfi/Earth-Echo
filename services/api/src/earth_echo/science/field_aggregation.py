"""Area weighted4x4 ocean-cell means for the OISST1degree display."""
import numpy as np


def oisst_degree_means(native,latitudes):
    if native.shape!=(720,1440) or len(latitudes)!=720:raise ValueError('Expected native OISST quarter-degree raster')
    grouped=np.ma.masked_invalid(native).reshape(180,4,360,4).transpose(0,2,1,3)
    weights=np.broadcast_to(np.cos(np.deg2rad(np.asarray(latitudes,dtype=np.float64)))[:,None],(720,1440)).reshape(180,4,360,4).transpose(0,2,1,3)
    count=np.ma.count(grouped,axis=(2,3))
    means=np.ma.average(grouped.astype(np.float64),weights=weights,axis=(2,3))
    # Display only when at least half of the16native cells are valid. The
    # original full-resolution field/mask remains accessible in the shared NC.
    return means,count
