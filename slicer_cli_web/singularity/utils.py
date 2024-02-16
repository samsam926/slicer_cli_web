def is_valid_image_name_format(image_str:str):
    '''
    This function is used to validate whether the user supplied a valid string <img>:<tag> as an argument for functions like singularity pull
    
    Args:
    image_str(str, required) - The string that needs to be validated.

    Returns:
    bool - True if the image is in a valid format, False otherwise.
    '''
    if not image_str:
        return False
    return True if len(image_str.split(':')) == 2 else False


def generate_image_name_for_singularity(image_str:str):
    '''
    We need to generate the image name for storing the .sif files on the filesystem so that it is standardized, so it can be referenced in future calls. 
    
    Args: 
    image_str (str,required) - the image_name in the format <img>:<tag>

    Return:
    str - A string that is to be used for the .sif filename
    '''
    if not is_valid_image_name_format(image_str):
        raise Exception('Not a valid image name. Please pass the image name in the format')
    image_str = image_str.replace('/','_').replace(':','_')
    return f"{image_str}.sif"
