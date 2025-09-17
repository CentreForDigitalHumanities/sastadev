from sastadev.conf import settings

pre_process_str, core_process_str, post_process_str, form_process_str = 'pre', 'core', 'post', 'form'
pre_process, core_process, post_process, form_process = 0, 1, 2, 3


def getprocess(process):
    if process.lower() == core_process_str:
        result = core_process
    elif process.lower() == post_process_str:
        result = post_process
    elif process.lower() == pre_process_str:
        result = pre_process
    elif process.lower() == form_process_str:
        result = form_process
    else:
        result = -1
        settings.LOGGER.error('Illegal value for process {}'.format(process))
    return result


def clean(valstr):
    result = valstr.strip().lower()
    return result


class Query:
    def __init__(self, id, cat, subcat, level, item, altitems, implies, original, pages, fase, query, inform,
                 screening, process, literal, stars, filter, variants, unused1, unused2, comments):
        self.id = id             # identifier of the query. so far of the form[TSA][0-9]{3,3}
        self.cat = cat           # a category for grouping  queries
        self.subcat = subcat     # a subcategory for grouping  queries
        self.level = level       # a different category for grouping queries
        self.item = item         # code to annotate a result of this query
        self.altitems = altitems # alternative codes that can be used to annotate a result of this query
        self.implies = implies   # obsolete, not needed anymore
        self.original = original # whether it is a query that occurs originally in the method definition or has been
                                 # added
        self.pages = pages      # page numbers where the query is described in the defining books/ documents
        self.fase = fase        # stage that this query belongs to (relevant for Tarsp only
        self.query = query      # the actual query, a Xpath expression, possibly with macros, or the name of a python
                                # function
        self.inform = inform    # does the query apear in the form ('profielkaart', profile chart) associated with the
        # method
        self.screening = screening # is the query part of the Tarsp screening procedure
        self.process = getprocess(process)  # pre, core or post. pre queries are applied before core queries,
                                            # and these before post queries
        self.literal = literal   # function to obtain the value part of the resultskey (QId, str). e..g to obtain the
                                 # lemma of  word
        self.stars = clean(stars) # whther the Tarsp code contains stars (asterisks)
        self.filter = filter    # boolean function used to filter results depending on results of other queies
        self.variants = variants  # to specify the variant(s) of the method that the query belongs to
        self.unused1 = unused1   # for future extensions
        self.unused2 = unused2  # for future extensions
        self.comments = comments  # free text comments


def query_inform(query):
    result = query.inform == "yes"
    return result


def is_preorcore(query):
    result = is_pre(query) or is_core(query)
    return result


def is_pre(query):
    result = (query.process == pre_process)
    return result


def is_core(query):
    result = (query.process == core_process)
    return result


def is_post(query):
    result = (query.process == post_process)
    return result


def query_exists(query):
    result = query.query != "" and query.query is not None
    return result


def is_literal(query):
    result = query.literal != ''
    return result
