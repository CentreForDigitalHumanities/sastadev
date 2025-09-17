from dataclasses import dataclass
import os
from sastadev.conf import settings
from sastadev.sastatypes import MethodName
from sastadev.xlsx import getxlsxdata
from typing import List, Tuple, Dict

comma = ','
space = ' '
MethodVariant = str
training = 'training'
testing = 'testing'


namecol = 0
methodcol = 1
usecol = 2
infigurescol = 3
variantcol = 4
samplecountcol = 5
bronzecountcol = 6
source_orgcol = 7
source_personscol = 8
descriptioncol = 9



datasetfilename = 'DatasetOverview.xlsx'
datasetfolder = settings.DATAROOT
datasetfullname = os.path.join(datasetfolder, datasetfilename)


def robustint(x) -> int:
    if x == '' or x == space:
        result = 0
    else:
        result = int(x)
    return result


@dataclass
class DataSet:
    rawname: str
    name: str
    method: MethodName
    use: str
    infigures: bool
    variant:  MethodVariant
    samplecount: int
    bronzecount: int
    source_org: str
    source_persons: Tuple[str]
    description: str


def row2dataset(row: List[str]) -> DataSet:
    rawname = row[namecol].strip()
    name = row[namecol].lower().strip()
    method = row[methodcol].lower().strip()
    use = row[usecol].lower().strip()
    infigures = True if row[infigurescol].lower() == 'yes' else False
    variant = row[variantcol].lower().strip()
    samplecount = robustint(row[samplecountcol])
    bronzecount = robustint(row[bronzecountcol])
    source_org = row[source_orgcol].strip()
    source_persons = tuple(row[source_personscol].split(comma))
    description = row[descriptioncol]
    result = DataSet(rawname= rawname, name=name, method=method, use=use, infigures=infigures, variant=variant, samplecount=samplecount,
                     bronzecount=bronzecount, source_org=source_org, source_persons=source_persons,
                     description=description)
    return result



def getalldatasets() -> List[DataSet]:
    datasets: List[DataSet] = []
    header, data = getxlsxdata(datasetfullname)
    for row in data:
        newdataset = row2dataset(row)
        datasets.append(newdataset)
    return datasets

alldatasets = getalldatasets()
infiguresdatasets = [d for d in alldatasets if d.infigures]
dsname2method = {d.name: d.method for d in alldatasets}
dsname2ds: Dict[str, DataSet] = {d.name: d for d in alldatasets}



trainingdatasets = [ds for ds in alldatasets if ds.use == training]
testdatasets = [ds for ds in alldatasets if ds.use == testing]
