import cv2
import numpy as np


def sklm(data_list, template, forgetting_factor):
    """
    Sequential Karhunen-Loeve Transform.

    Parameters
    ----------
    data_list : list
        List of new data vectors to incorporate
    template : dict
        Template parameters containing:
        - basis: Previous basis matrix
        - eigval: Previous singular values
        - mean: Previous sample mean
        - nsamples: Number of previous data points
    forgetting_factor : float
        Factor controlling influence of previous data (0-1)

    Returns
    -------
    basis : ndarray
        Updated basis matrix
    singular_values : ndarray
        Updated singular values
    mean_vector : ndarray
        Updated mean vector
    effective_samples : float
        Effective number of samples
    """

    previous_basis = template["basis"]
    previous_values = template["eigval"]
    previous_mean = template["mean"]
    previous_samples = template["nsamples"]

    feature_dim = data_list[0].size
    new_samples = len(data_list)

    data_matrix = np.array(data_list, dtype=np.float32).T

    if previous_basis.shape[1] == 0:
        mean_vector = np.mean(data_matrix, axis=1, dtype=np.float32)
        centered_data = data_matrix - mean_vector[:, np.newaxis]

        basis, singular_values, _ = np.linalg.svd(centered_data, full_matrices=False)
        return basis, singular_values, mean_vector, float(new_samples)

    new_mean = np.mean(data_matrix, axis=1, dtype=np.float32)
    centered_data = data_matrix - new_mean[:, np.newaxis]

    weighted_total = (forgetting_factor * previous_samples) + new_samples
    weight_previous = (forgetting_factor * previous_samples) / weighted_total
    weight_new = new_samples / weighted_total

    mean_vector = weight_previous * previous_mean + weight_new * new_mean

    harmonic_mean = (new_samples * previous_samples) / float(new_samples + previous_samples)
    mean_diff = np.sqrt(harmonic_mean) * (new_mean - previous_mean)

    augmented_data = np.zeros((feature_dim, new_samples + 1), dtype=np.float32)
    augmented_data[:, :new_samples] = centered_data
    augmented_data[:, new_samples] = mean_diff

    effective_samples = new_samples + forgetting_factor * previous_samples

    projection = previous_basis.T @ augmented_data
    orthogonal_comp = augmented_data - previous_basis @ projection

    orth_basis, _ = np.linalg.qr(orthogonal_comp, mode="reduced")
    combined_basis = np.hstack((previous_basis, orth_basis))

    t1 = np.diag(previous_values * forgetting_factor)
    t2 = projection
    t3 = np.zeros((orth_basis.shape[1], previous_values.size), dtype=np.float32)
    t4 = orth_basis.T @ orthogonal_comp

    r_height = t1.shape[0] + t3.shape[0]
    r_width = t1.shape[1] + t2.shape[1]
    r_matrix = np.zeros((r_height, r_width), dtype=np.float32)

    r_matrix[:t1.shape[0], :t1.shape[1]] = t1
    r_matrix[:t2.shape[0], t1.shape[1]:] = t2
    r_matrix[t1.shape[0]:, :t3.shape[1]] = t3
    r_matrix[t1.shape[0]:, t3.shape[1]:] = t4

    u_small, singular_values, _ = np.linalg.svd(r_matrix, full_matrices=False)

    cutoff = np.linalg.norm(singular_values) * 0.001
    significant_indices = singular_values >= cutoff
    singular_values = singular_values[significant_indices]

    basis = combined_basis @ u_small[:, significant_indices]

    return basis, singular_values, mean_vector, effective_samples


def warp_multiple_images(image, state_params, target_size):
    """
    Warp multiple images based on state parameters.

    Parameters
    ----------
    image : ndarray
        Input image
    state_params : ndarray
        Array of state parameters, shape (n_samples, 5) where each row contains
        [center_x, center_y, scale, aspect_ratio, angle]
    target_size : tuple
        Target size (width, height) for output images

    Returns
    -------
    ndarray
        Array of warped images with shape (target_height, target_width, n_samples)
    """

    if state_params.ndim == 1:
        state_params = state_params.reshape(1, -1)

    target_width, target_height = target_size
    n_samples = state_params.shape[0]

    warped_images = np.zeros(
        (target_height, target_width, n_samples),
        dtype=image.dtype,
    )

    for i in range(n_samples):
        warped_images[:, :, i] = warp_image(image, state_params[i], target_size)

    return warped_images


def warp_image(image, state_params, target_size):
    """
    Warp image based on state parameters.

    Parameters
    ----------
    image : ndarray
        Input image to be warped
    state_params : ndarray
        State parameters in format [center_x, center_y, scale, aspect_ratio, angle]
        where angle is optional
    target_size : tuple
        Target size (width, height) for output image

    Returns
    -------
    ndarray
        Warped and resized image
    """

    center = (state_params[0], state_params[1])

    width = state_params[2] * target_size[0]
    height = state_params[3] * width

    angle = 0.0

    if len(state_params) > 4:
        angle = state_params[4]

    return extract_subimage(image, center, width, height, target_size, angle)


def extract_subimage(image, center, width, height, target_size, angle=0.0):
    """
    Extract and resize a rotated subimage from the input image.

    Parameters
    ----------
    image : ndarray
        Input image
    center : tuple
        Center point of extraction (cx, cy)
    width : float
        Width of region to extract
    height : float
        Height of region to extract
    target_size : tuple
        Target size (width, height) for output image
    angle : float, optional
        Rotation angle in radians, default is 0.0

    Returns
    -------
    ndarray
        Extracted and resized subimage
    """

    image_height, image_width = image.shape[:2]
    target_width, target_height = target_size

    cx, cy = int(np.round(center[0])), int(np.round(center[1]))
    width, height = int(np.round(width)), int(np.round(height))

    if np.abs(angle) > 1e-5:
        rotation_degrees = -np.rad2deg(angle)
        rotation_matrix = cv2.getRotationMatrix2D((cx, cy), rotation_degrees, 1.0)

        processed_image = cv2.warpAffine(
            image,
            rotation_matrix,
            (image_width, image_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT
        )
    else:
        processed_image = image

    half_width = width // 2
    half_height = height // 2

    left = cx - half_width
    top = cy - half_height
    right = left + width
    bottom = top + height

    left = np.max(0, left)
    top = np.max(0, top)
    right = np.min(image_width, right)
    bottom = np.min(image_height, bottom)

    channels = 1
    output_shape = None

    if len(image.shape) > 2:
        channels = image.shape[2]

    if channels > 1:
        output_shape = (target_height, target_width, channels)
    else:
        output_shape = (target_height, target_width)

    if left >= right or top >= bottom:
        return np.zeros(output_shape, dtype=image.dtype)

    extracted_region = processed_image[top:bottom, left:right]

    if extracted_region.size == 0:
        return np.zeros(output_shape, dtype=image.dtype)

    current_height, current_width = extracted_region.shape[:2]

    if current_height != target_height or current_width != target_width:
        return cv2.resize(
            extracted_region,
            (target_width, target_height),
            interpolation=cv2.INTER_LINEAR,
        )

    return extracted_region
