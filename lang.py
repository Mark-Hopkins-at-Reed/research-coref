class Sentence:
    """
    Representation of a sentence with annotated coreferences.
    
    Tokens is a list of the sentence tokens.
    References is a list of triples of the form 
    (entity_id, start_span, end_span). This means that the entity with
    the indicated id is referenced beginning at start_span and ending
    at end_span.
    
    """
    
    def __init__(self, tokens, references):
        self.tokens = self.normalize(tokens)
        self.references = references
        
    def __str__(self):
        return ' '.join(self.tokens)
    
    def normalize(self, tokens):
        normalized = []
        for tok in tokens:
            revised = tok
            if tok == '-LRB-':
                revised = '('
            elif tok == '-RRB-':
                revised = ')'
            normalized.append(revised)
        return normalized


class Document:
    """
    Representation of a document with annotated coreferences.
    
    doc_id is a string identifier for the document.
    tokens is a list of lists, such that tokens[i][j] is the jth token
      of the ith sentence of the document.
    mentions is a list of coreference clusters, where a coreference
      cluster is a list of tuples (sent_num, span_start, span_end).
      Each tuple in a coreference cluster refers to the same entity.
      Thus, if (2,5,6) and (7,9,13) appear in the same cluster, then
      the same entity is referred to by span [5,6] of sentence 2 and
      span [9,13] of sentence 7.
    
    """
    def __init__(self, doc_id, tokens, mentions):
        self.doc_id = doc_id
        self.tokens = tokens
        self.mentions = mentions
        
    def __str__(self):
        sents = ['(' + str(i) + ') ' + ' '.join(sent_toks) for 
                 (i, sent_toks) in enumerate(self.tokens)]
        corefs = [str(cluster) for cluster in self.mentions]
        return '\n'.join(sents) + '\n' + '\n'.join(corefs)
    
    def to_json_datum(self):
        result = dict()
        result['id'] = self.doc_id
        result['sentences'] = self.tokens
        result['corefs'] = self.mentions
        return result
 
