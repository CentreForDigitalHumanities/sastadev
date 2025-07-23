from persistentcomments import PersistentComments, FileDescription
from sastadev.conf import settings
from sastadev.constants import checksuffix, errorsummaryfolder, errorsummarysuffix, permprefix, silverpermfolder, resultsfolder
import os

def ischeckfile(fn: str) -> bool:
    result = fn.endswith(f'{checksuffix}.xlsx')
    return result

def iserrorsummaryfile(fn: str) -> bool:
    result = fn.endswith(f'{errorsummarysuffix}.xlsx')
    return result



def main():
    dataset = 'auristrain'

    # checkfiles
    resultspath = os.path.join(settings.DATAROOT, dataset, resultsfolder)
    filedescription1 = FileDescription([resultspath], ischeckfile)

    # errorsummaryfiles
    errorsummarypath  = os.path.join(settings.DATAROOT, dataset, errorsummaryfolder)
    filedescription2 = FileDescription([errorsummarypath], iserrorsummaryfile)

    # add the analaysiscomparison checkfiles
    # to be done

    pc1filedescriptions = [filedescription1, filedescription2]
    pc1persistentcommentsfolder = os.path.join(settings.DATAROOT, dataset, silverpermfolder)
    pc1mkpersistentfilename = lambda dataset: f'{permprefix}{dataset}.xlsx'
    pc1keycolumns = [0, 5, 10, 11, 4]
    pc1commentscolumns = [1, 2, 3]

    pc1 = PersistentComments(filedescriptions=pc1filedescriptions, persistentcommentsfolder=pc1persistentcommentsfolder,
                             mkpersistentfilename=pc1mkpersistentfilename, keycolumns=pc1keycolumns,
                             commentscolumns=pc1commentscolumns)

    permdatadict = pc1.getallcomments(dataset)

if __name__ == '__main__':
    main()