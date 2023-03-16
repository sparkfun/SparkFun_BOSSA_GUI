from .au_action import AxAction, AxJob
from .SAMBALoad import startLoaderCommand as loader


#--------------------------------------------------------------------------------------
# action testing
class AUxSAMBADetect(AxAction):

    ACTION_ID = "samba-detect"
    NAME = "Processor Detection"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob, info):

        try:
            sysExit, message = loader(job.command)

            info.append({'Detected Part' : 'Fred'})

            #if 'Detected Part: ' in message:
            #    info.append({'Detected Part': message[(message.find('Detected Part: ') + len('Detected Part: ')):]})

        except Exception:
            return 1

        if sysExit > 0:
            return 1
        
        return 0

class AUxSAMBAErase(AxAction):

    ACTION_ID = "samba-erase"
    NAME = "Erase Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob, info):

        try:
            sysExit, message = loader(job.command)
        except Exception:
            return 1

        if sysExit > 0:
            return 1
        
        return 0

class AUxSAMBAProgram(AxAction):

    ACTION_ID = "samba-program"
    NAME = "Program Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob, info):

        try:
            sysExit, message = loader(job.command)

        except Exception:
            return 1

        if sysExit > 0:
            return 1
        
        return 0

class AUxSAMBAVerify(AxAction):

    ACTION_ID = "samba-verify"
    NAME = "Verify Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob, info):

        try:
            sysExit, message = loader(job.command)

        except Exception:
            return 1

        if sysExit > 0:
            return 1
        
        return 0

class AUxSAMBAReset(AxAction):

    ACTION_ID = "samba-reset"
    NAME = "Reset Processor"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob, info):

        try:
            sysExit, message = loader(job.command)

        except Exception:
            return 1

        if sysExit > 0:
            return 1
        
        return 0
        