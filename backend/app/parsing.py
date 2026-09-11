"""Untrusted document parsing runs in a bounded child process, never executes content."""
import io, multiprocessing, zipfile
from pathlib import Path
from .config import MAX_BYTES,MAX_TEXT

def _extract(data,ext,conn):
    try:
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU,(8,8))
            resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
        except (ImportError,ValueError): pass
        if ext=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(data))
            if reader.is_encrypted: raise ValueError('Encrypted PDFs are not supported.')
            if len(reader.pages)>30: raise ValueError('Maximum 30 PDF pages.')
            parts=[]
            for page in reader.pages:
                parts.append(page.extract_text() or '')
                if sum(map(len,parts))>MAX_TEXT: raise ValueError('Document exceeds 40,000 characters.')
            text='\n'.join(parts)
        elif ext=='.docx':
            from docx import Document
            doc=Document(io.BytesIO(data));parts=[]
            # Preserve paragraph/table reading order rather than appending all tables last.
            from docx.text.paragraph import Paragraph
            from docx.table import Table
            for child in doc.element.body.iterchildren():
                if child.tag.endswith('}p'): parts.append(Paragraph(child,doc).text)
                elif child.tag.endswith('}tbl'): parts += [' | '.join(c.text for c in row.cells) for row in Table(child,doc).rows]
            text='\n'.join(parts)
        else: text=data.decode('utf-8')
        if not text.strip(): raise ValueError('No selectable text found. Run OCR on scanned files first.')
        if len(text)>MAX_TEXT: raise ValueError('Document exceeds 40,000 characters.')
        conn.send({'text':text})
    except Exception as exc: conn.send({'error':str(exc) if isinstance(exc,ValueError) else 'Malformed or unsupported document.'})
    finally: conn.close()

def parse_file(data:bytes,filename:str,allow_txt=False):
    if not data: raise ValueError('The uploaded file is empty.')
    if len(data)>MAX_BYTES: raise ValueError('File exceeds the 5 MB limit.')
    ext=Path(filename).suffix.lower()
    if ext not in (['.pdf','.docx','.txt'] if allow_txt else ['.pdf','.docx']): raise ValueError('Upload a PDF or DOCX'+(' or TXT' if allow_txt else '')+'.')
    if ext=='.pdf' and not data.startswith(b'%PDF-'): raise ValueError('File signature is not PDF.')
    if ext=='.docx':
        if not data.startswith(b'PK'): raise ValueError('File signature is not DOCX.')
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos=z.infolist()
                if len(infos)>2000 or sum(i.file_size for i in infos)>20*1024*1024: raise ValueError('DOCX archive expands beyond safe limits.')
                if 'word/document.xml' not in z.namelist(): raise ValueError('Invalid DOCX document.')
                if any('vbaproject' in i.filename.lower() or i.filename.startswith('/') or '..' in Path(i.filename).parts for i in infos): raise ValueError('Unsafe document archive.')
        except zipfile.BadZipFile: raise ValueError('Invalid DOCX archive.')
    ctx=multiprocessing.get_context('spawn');parent,child=ctx.Pipe(False)
    process=ctx.Process(target=_extract,args=(data,ext,child));process.start();child.close()
    try:
        if not parent.poll(12): raise ValueError('Document parsing exceeded the time limit.')
        try: result=parent.recv()
        except EOFError: raise ValueError('Document parser could not safely read this file.')
        if 'error' in result: raise ValueError(result['error'])
        return result['text']
    finally:
        if process.is_alive(): process.terminate()
        process.join(timeout=2);parent.close()
