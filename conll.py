from collections import defaultdict
from lang import Sentence, Document
import os
import json

class ConllChunk:
    """
    A ConllChunk is an abstract class that represents a chunk of a CoNLL
    file for coreference resolution. The file format is desribed here:
        
        http://conll.cemantix.org/2012/data.html
    
    """    
    def conll_type(self):
        raise NotImplementedError('Cannot instantiate the abstract class.')

class BeginDocument(ConllChunk):
    """Signals the beginning of a document called 'doc_id'."""    
    def __init__(self, doc_id):
        self.doc_id = doc_id

    def conll_type(self):
        return "begin"

class EndDocument(ConllChunk):
    """Signals the end of a document."""        
    def __init__(self):
        pass

    def conll_type(self):
        return "end"

class EndFile(ConllChunk):
    """Signals the end of a CoNLL file."""        
    def __init__(self):
        pass

    def conll_type(self):
        return "eof"


class Segment(ConllChunk):
    """
    Lines representing a segment in a CoNLL file.
    
    Each line correponds to a single token in the segment. The line has
    the following whitespace-separated columns:
        
        Column	Type	       
        1	    Document ID	
        2	    Part number
        3	    Word number	
        4	    Word itself
        5	    Part-of-Speech	
        6	    Parse bit
        7	    Predicate lemma
        8	    Predicate Frameset ID
        9	    Word sense
        10	    Speaker/Author
        11	    Named Entities
        12:N	    Predicate Arguments
        N	    Coreference
    
    """        
    def __init__(self, lines):
        self.lines = lines

    def conll_type(self):
        return "segment"
    
    def __str__(self):
        return '\n'.join(self.lines)



def read_conll_chunk(inhandle):
    """
    This reads the next ConllChunk from an open file handle and returns it.
    
    """
    firstline = inhandle.readline()
    if firstline.strip() == '':
        return EndFile() 
    elif firstline.startswith("#begin document"):
        doc_id = firstline[len("#begin document"):].strip()
        return BeginDocument(doc_id)
    elif firstline.startswith("#end document"):
        return EndDocument()
    else:                      
        lines = [firstline]
        for line in inhandle:
            if line.strip() == '':
                break
            else:
                lines.append(line.strip())
        return Segment(lines)


def read_conll_document(inhandle):
    """
    Given an open file handle, this reads the next document. It is assumed
    that the next chunks read by read_conll_chunk should be:
        
        - 1 BeginDocument
        - 1 or more Segments
        - 1 EndDocument
        
    It will return the document id and a list of the Segments.
    
    """
    firstchunk = read_conll_chunk(inhandle)
    if firstchunk.conll_type() == 'eof':
        return (None, None)
    if not firstchunk.conll_type() == 'begin':
        raise Exception('Unexpected chunk: {}'.format(firstchunk))
    nextchunk = read_conll_chunk(inhandle)
    chunks = []
    while nextchunk.conll_type() == 'segment':
        chunks.append(nextchunk)    
        nextchunk = read_conll_chunk(inhandle)
    if not nextchunk.conll_type() == 'end':
        raise Exception('Unexpected chunk: {}'.format(nextchunk))
    return (firstchunk.doc_id, chunks)
                           


       
def read_conll_file(filename):
    """
    From a CoNLL file, this creates a generator such that every call to
    'next' returns the next lang.Document encoded by the file.
    
    e.g.
    > gen = read_conll_file('foo.conll')
    > next(gen)
    <lang.Document at 0x123ac85c0>
    > next(gen)
    <lang.Document at 0x123a747b8>
    
    """
    
    def process_conll_document(doc_id, sents):
        mentions = defaultdict(list)
        for i, sent in enumerate(sents):
            for (entity, start, stop) in sent.references:
                mentions[entity].append((i, start, stop))
        tokens = [sent.tokens for sent in sents]
        corefs = list(mentions.values())
        return Document(doc_id, tokens, corefs)
            
    def process_conll_sentence(sent):
        tokens = []
        open_list = []
        spans = []
        for line in sent.lines:
            fields = line.split()
            word_position = int(fields[2].strip())
            corefs = fields[-1].strip().split('|')
            for coref in corefs:
                if coref.startswith('(') and coref.endswith(')'):
                    entity = int(coref[1:-1])
                    spans.append((entity, word_position, word_position))
                elif coref.startswith('('):
                    entity = int(coref[1:])
                    open_list = [(entity, word_position)] + open_list             
                elif coref.endswith(')'):
                    entity = int(coref[:-1])
                    _, start_position = next(x for x in open_list if x[0] == entity)
                    spans.append((entity, start_position, word_position))
                    open_list.remove((entity, start_position))           
                               
            tokens.append(fields[3].strip())
        return Sentence(tokens, spans)

    with open(filename) as inhandle:
        has_more = True
        while has_more:
            (doc_id, chunks) = read_conll_document(inhandle)
            if doc_id is None:
                has_more = False
            else:
                sents = [process_conll_sentence(chunk) for chunk in chunks]
                yield process_conll_document(doc_id, sents)
        
    

TRAIN_DIR = '/Users/hopkinsm/Projects/data/coref/conll2012/conll-2012/v4/data/train/data/english/annotations'      
DEV_DIR = '/Users/hopkinsm/Projects/data/coref/conll2012/conll-2012/v4/data/development/data/english/annotations'
                
def harvest(root_dir, output_file):
    """
    Walks through the directory structure of the specified root directory,
    finds all CoNLL files, and harvests the encoded lang.Documents.
    
    These lang.Documents are then written to a JSON file.
    
    """
    docs = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith("gold_conll"):                
                filename = os.path.join(root, file)     
                print(filename)
                for doc in read_conll_file(filename):
                    docs.append(doc.to_json_datum())
    with open(output_file, 'w') as outhandle:
        outhandle.write(json.dumps(docs, indent=4, sort_keys=True))
    
                