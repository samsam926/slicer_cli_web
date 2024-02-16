'''
This file deals with all the helper functions to add help with adding singularity functionality to slicer_cli_web  
'''

SINGULARITY_COMMANDS  = {
    'PULL': 0
}

def singularity_cmd_list(cmd):
    def singularity_pull(imageName):
        return f"singularity pull {imageName}.sif docker://{imageName}"
    if cmd == SINGULARITY_COMMANDS['PULL']:
        return singularity_pull