import pynvim
import langchain
from pygments.util import ClassNotFound
from pygments.lexers import guess_lexer_for_filename, TextLexer
from langchain.cache import InMemoryCache
from langchain.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class IA():
    def __init__(self,):
        langchain.llm_cache = InMemoryCache()
        LLAMA_EMBEDDINGS_MODEL = '/Users/matheus.bernardes/dev/mthbernardes/code-query/models/ggml-model-q4_0.bin' 
        MODEL_N_CTX = 1000
        CALLBACKS = [StreamingStdOutCallbackHandler()]
        PROMPT_TEMPLATE = """This is a piece of {language} code. I need a detailed line-by-line explanation of what it does and identification of any potential security vulnerabilities or coding bad practices. Here's the code:
        ```
        {code}
        ```
        Please provide a detailed walkthrough of its operation and highlight any sections of the code that could potentially lead to security risks or inefficiencies.
        """

        PROMPT = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["language","code"])
        LLM = LlamaCpp(model_path=LLAMA_EMBEDDINGS_MODEL, n_ctx=MODEL_N_CTX, verbose=False)
        self.CHAIN = LLMChain(llm=LLM, prompt=PROMPT)

    def run(self, input):
        explained = self.CHAIN.run(input)
        lines = explained.split('\n')
        return lines

@pynvim.plugin
class CodeExplain(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.codeExplainAI = IA()
        self.nvim.command("echom \"My plugin is being executed\"")
    
    def getSelectedText(self,):
        begin = self.nvim.eval("line(\"'<\")")
        end = self.nvim.eval("line(\"'>\")")
        lines = self.nvim.current.buffer[begin - 1:end]
        return '\n'.join(lines)

    def getProgrammingLanguage(self):
        file_name = self.nvim.current.buffer.name
        file_content = '\n'.join(self.nvim.current.buffer[:])
        try:
            lexer = guess_lexer_for_filename(file_name, file_content)
        except ClassNotFound:
            lexer = TextLexer()
        return lexer.name

    def createWindowBuffer(self,lines):
        bufnr = self.nvim.api.create_buf(False, True)
        winnr = self.nvim.api.open_win(bufnr, True, {
            'relative': 'editor',
            'width': 80,
            'height': 10,
            'row': 10,
            'col': 10
        })
        self.nvim.api.buf_set_lines(bufnr, 0, -1, True, lines)

    @pynvim.command('CodeExplain', nargs='*',range=True, sync=True)
    def codeExplain(self,args,range):
        selected_text = self.getSelectedText()
        programming_language = self.getProgrammingLanguage() or "programming"
        explained = self.codeExplainAI.run({"language": programming_language,"code":selected_text})
        lines = [self.nvim.funcs.escape(line, '\"\\') for line in explained]
        self.createWindowBuffer(explained)
