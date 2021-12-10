import warnings
import os
from os.path import join, basename
import numpy as np
import rasterio as rio
import rasterio.mask
import fiona
from rasterio.enums import Resampling
import geopandas as gpd
from shapely.geometry import Polygon
import cv2
import seaborn as sns
import matplotlib.pyplot as plt


def raster_resample(raster_path, rescale_factor, out_dir):
    '''https://rasterio.readthedocs.io/en/latest/topics/resampling.html
    
    raster : raster path
    resample_rate : float, >1 -upsampling, <1 -downsampling
    out_dir : folder path for writing the raster files
    '''

    src = rio.open(raster_path)

    data = src.read(                                    # type: ignore
        out_shape=(
            src.count,                                  # type: ignore
            int(src.height * rescale_factor),           # type: ignore
            int(src.width * rescale_factor)             # type: ignore
        ),
        resampling=Resampling.average #nearest # bilinear, #cubic
    )

    # scale image transform
    transform = src.transform * src.transform.scale(    # type: ignore
        (src.width / data.shape[-1]),                   # type: ignore
        (src.height / data.shape[-2])                   # type: ignore
    )

    out_meta = src.meta.copy()                          # type: ignore
    out_meta.update({
        'driver': 'GTiff',
        'width': data.shape[2],
        'height': data.shape[1],
        'crs': src.meta['crs'],                         # type: ignore
        'transform': transform,
        'count': data.shape[0]
    })

    # name = basename(raster).split('.')[0] + '_res' + '.tif'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)  # make directory
    name = join(basename(raster_path).split('.')[0], '_resampled')
    output_raster = join(out_dir, name)

    with rio.open(output_raster, 'w', **out_meta) as dest:
        dest.write(data)
    print(output_raster)


def raster_extent2shp(raster, out_dir):
    ''' Vectorizes the raster extent and writes as a shapfile 
    '''
    # name = basename(raster)
    name = basename(raster).split('.')[0] + '.shp'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)  # make directory
    out_shp_name = join(out_dir, name)

    src = rio.open(raster)
    bounds = src.bounds                                 # type: ignore
    xmin = bounds.left
    ymin = bounds.bottom
    xmax = bounds.right
    ymax = bounds.top

    lat_points = [ymax, ymax, ymin, ymin, ymax]
    lon_points = [xmin, xmax, xmax, xmin, xmin]

    polygon_geom = Polygon(zip(lon_points, lat_points))
    # crs = {'init': 'epsg:4326'}
    crs = src.meta['crs']                               # type: ignore
    polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
    polygon.to_file(filename=out_shp_name, driver="ESRI Shapefile")
    print(out_shp_name)


def im_resize(img, dsize, interpolation):
    ''' Resize the image with given 2d sizes and interpolation method: 

    Parameters
    ----------
   
    dsize:  tuple, dimensions of each image.
            Note: for cv2 lib. array dimensions are different from np.array
    interpolation:  resampling method,
            for upscaling - cv2.INTER_CUBIC, #INTER_LINEAR (faster). 
                            #cv2.INTER_NEAREST,
            for downscaling - cv2.INTER_AREA
    
    Note: it's the opposite of numpy array dimensions. In case of cv2 
          the 0-axe is considered the columns, and the 1-axe is rows

    Returns
    -------
    2d array
    '''
    dim1 = dsize[1]
    dim2 = dsize[0]

    resized = cv2.resize(img, dsize=(dim1, dim2),       # type: ignore
                         interpolation=interpolation)   # resampling_alg=1
    return resized


def glcm_texture(im, window, prop, gray_levels=32, normed=True):
    '''Applies glcm texture functions over given size window
    and returns the sum of the resulting texture per window
    
    Parameters
    ----------
    im : 2D array
    window : tuple of integers defining rows and cols of the window
    prop : glcm property to be calculated
    gray_levels : Number of gray levels for image pixel quantization
    normed: bool, optional
            If True, normalize each matrix `P[:, :, d, theta]` by dividing
            by the total number of accumulated co-occurrences for the given
            offset. The elements of the resulting matrix sum to 1.
    rescale: bool, optional,
            defines if the image array should be normalized with min-max 
            befor the glcm calculation. Default is True.

    Note: the edges of image not compliting an window will be excluded
    
    Returns
    -------
    out : 2D array
    '''
    from skimage.feature import greycomatrix, greycoprops
    from skimage.measure import shannon_entropy
    # from sklearn.metrics.cluster import entropy

    image = im  # .copy()
    y, x = window
    out = []
    i_num = []
    for i in range(0, image.shape[0], y):
        j_num = []
        for j in range(0, image.shape[1], x):
            # get the window
            sub_image = image[i:i+y, j:j+x]

            #============================
            # apply greycomatrix function
            #============================
            # scale the image values according to the gray levles
            sub_image /= sub_image.max()/(gray_levels-1)
            scaled = (np.round_(sub_image, 0)).astype(int)

            # calculate Gray Level Co-occurance Matrix
            glcm = greycomatrix(
                scaled, 
                [1], 
                [0, np.pi/4, np.pi/2, 3*np.pi/4], 
                normed=normed, 
                levels=gray_levels, 
                symmetric=True)
            # glcm = greycomatrix(scaled, [1], [0, np.pi/2], normed=normed, levels=gray_levels)

            # calculate texture measures from glcm
            if prop == 'dissimilarity':
                texture = greycoprops(glcm, prop='dissimilarity')
            elif prop == 'homogeneity':
                texture = greycoprops(glcm, prop='homogeneity')
            elif prop == 'entropy':
                glcm_sqz = glcm.squeeze()
                ls_ent = [shannon_entropy(glcm_sqz[:, :, i], base=np.e)
                          for i in range(4)]
                texture = np.mean(ls_ent)
                # texture = shannon_entropy(glcm, base=np.e)
                # texture = entropy(glcm)
            else:
                raise ValueError(
                    "Property should be defined as one of those:" 
                    "['entropy', 'dissimilarity','homogeneity']")

            # as the texture property is calculated for 4 directions,
            # we would need to average them for a single output
            out.append(texture.mean())

            j_num.append(j)
        i_num.append(i)

    # reshape to 2D array
    out_image = np.array(out).reshape(len(i_num), len(j_num)) # type: ignore
    return out_image


# Convert SAR backscattering DN to dB and vice bersa
def natural2dB(natural): return np.log10(natural)*10
def dB2natural(dB): return 10**(dB/10)


def add_indices(bands):
    '''Returns stack of original data and Indices: NDVI, NDWI, GVI
    
    The indices are multiplied by 10_000 to bring into the same scale 
    with image band values
    
    Note:   The function is specified for MODIS-2 images and 
            will result wrong data for other images'''
    
    ndvi = (bands[0, ...] - bands[1, ...]) / (bands[0, ...] + bands[1, ...])*1000
    ndwi = (bands[2, ...] - bands[0, ...]) / (bands[2, ...] + bands[0, ...])*1000
    gvi  = (bands[0, ...] - bands[2, ...]) / (bands[0, ...] + bands[2, ...])*1000
 
    return np.vstack((
        bands, 
        ndvi[np.newaxis, :], 
        ndwi[np.newaxis, :], 
        gvi[np.newaxis, :]
        ))


def make_correlation_matrix(df, corr_type='pearson', figsize=(10, 10)):
    sns.set_style('white')
    # Compute the correlation matrix
    corr = df.corr(corr_type)
    # Generate a mask for the upper triangle
    mask = np.triu(np.ones_like(corr, dtype=np.bool))       # type: ignore
    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=figsize)
    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 15, as_cmap=True)
    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})  # annot=True


def fill_nans(array):
    # Check for missing values and fill it
    if np.isnan(array).any():
        print('there are missing values')

        # Fill nan values with linear interpolation with nearest non-nan values
        mask = np.isnan(array)
        array[mask] = np.interp(np.flatnonzero(
            mask), np.flatnonzero(~mask), array[~mask])
    else:
        pass
    return array


def block_fn(x,center_val):

    unique_elements, counts_elements = np.unique(x.ravel(), return_counts=True)

    if np.isnan(center_val):
        return np.nan
    elif center_val == 1:
        return 1.0
    else:
        return unique_elements[np.argmax(counts_elements)]


def majority_filter(x, block_size = (3,3)):

    # Odd block sizes only (?)
    # for even size kernel it needs extra treatment for kernel center
    assert(block_size[0]%2 != 0 and block_size[1]%2 !=0)

    yy =int((block_size[0] - 1) / 2)
    xx =int((block_size[1] - 1) / 2)

    output= np.zeros_like(x)
    for i in range(0, x.shape[0]):
        miny,maxy = max(0, i-yy), min(x.shape[0]-1 , i+yy)

        for j in range(0, x.shape[1]):
            minx,maxx = max(0, j-xx), min(x.shape[1]-1, j+xx)

            #Extract block to take majority filter over
            block=x[miny:maxy+1, minx:maxx+1]

            output[i,j] = block_fn(block,center_val=x[i,j])
    return output


def write_raster(ndArray, src, dest_path):
    '''Write multi band raster from nd.array'''
    out_meta  = src.meta.copy()
    
    if len(ndArray.shape)==2:
        count = 1
    else:
        count = ndArray.shape[0]
        
    out_meta.update({
        "driver": "GTiff",
        "dtype" : 'float32',
        "nodata": None, #np.nan,
        "height": src.height,
        "width" : src.width,
        "transform": src.transform,
        "count" : count,
        "crs":  out_meta['crs']
    })

    # Write the array to raster GeoTIF 
    with rio.open(dest_path, "w", **out_meta) as dest:
        if len(ndArray.shape)==2:
            dest.write(ndArray,indexes=1)
        else:
            dest.write(ndArray)


def tiff_mask2shape(shape_path, tiff_path, dest_path):
    '''Mask raster with shapefile and write on the same raster file'''
    with fiona.open(shape_path, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile] # type: ignore

    with rio.open(tiff_path) as src:
        out_image, out_transform = rio.mask.mask(src, shapes, crop=True) # type: ignore
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rio.open(dest_path, "w", **out_meta) as dest:
        dest.write(out_image)