# this file handles parsing .gons for game data
# the GON format is a derivitive of JSON https://github.com/TylerGlaiel/GON
# the gon is parsed into a python object for ease-of-use

# as this is a translation of the original C++ code here is the license :)
# some liberty was taken to simpify the code.
# also some things needed to be changed since Mewgenics doesn't fully adhere to this
################################################################################
# MIT License

# Copyright (c) 2018 Tyler Glaiel

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
################################################################################

from typing import Any

class GON:
    @staticmethod
    def is_whitespace(char: str) -> bool:
        return char ==' ' or char == '\n' or char == '\r' or char == '\t'
    
    @staticmethod
    def is_symbol(char: str) -> bool:
        return char == '=' or char == ',' or char == '{' or char == '}' or char == '[' or char == ']'
    
    @staticmethod
    def is_ignored_symbol(char: str) -> bool:
        return char == '=' or char == ',' or char == ':'
    
    @staticmethod
    def on_error(error: str):
        # the original throws a raw std::string... if you know C++ you know you shouldn't do that.
        raise RuntimeError(error)
    
    @staticmethod
    def ends_with(string: str, suffix: str) -> bool:
        return string.endswith(suffix)
    
    @staticmethod
    def remove_suffix(string: str, suffix: str) -> str:
        return string.removesuffix(suffix)
    
    @staticmethod
    def tokenize(data: str) -> list[str]:
        tokens: list[str] = []

        inStr = False
        inComment = False
        inMultilineComment = False
        escaped = False
        curToken = ""
        
        i = -1 # using while so i += 1 works (for does not allow this)
        while (i + 1 < len(data)):
            i += 1

            char = data[i]
            if (not inStr and not inComment and not inMultilineComment):
                # great liberty was taken in rearranging this part
                symbol = GON.is_symbol(char)
                comment = char == '#' or (char == '/' and i + 1 < len(data) and data[i + 1] == '/')
                multilineComment = char == '/' and i + 1 < len(data) and data[i + 1] == '*'
                string = char == '"'

                if (symbol or comment or multilineComment or string or GON.is_whitespace(char)):
                    if (curToken != ""):
                        tokens.append(curToken)
                        curToken = ""

                    if (symbol and not GON.is_ignored_symbol(char)):
                        # symbol must be 1 char!
                        tokens.append(char)
                    elif (comment):
                        inComment = True
                        i += int(char == '/')
                    elif (multilineComment):
                        inMultilineComment = True
                        i += 1
                    elif (string):
                        inStr = True

                    continue

                curToken += char
                continue

            if (inStr):
                if (escaped):
                    # this only handles \n, ask Tyler Glaiel why, idk.
                    if (char == 'n'):
                        curToken += '\n'
                    else:
                        curToken += char
                    escaped = False
                elif (char == '\\'):
                    escaped = True
                elif (not escaped and char == '"'):
                    tokens.append(curToken)
                    curToken = ""
                    inStr = False
                    continue
                else:
                    curToken += char
                    continue

            if (inComment):
                if (char == '\n'):
                    tokens.append("//" + curToken)
                    curToken = ""
                    inComment = False
                    continue

                curToken += char
                continue

            if (inMultilineComment):
                if (char == '*' and i + 1 < len(data) and data[i + 1] == '/'):
                    tokens.append("//" + curToken)
                    curToken = ""
                    inMultilineComment = False
                    i += 1
                    continue

                curToken += char
                continue


        if (curToken != ""):
            if (inComment): # this is legal, strings and others aren't
                tokens.append("//" + curToken)
            else:
                tokens.append(curToken)

        return tokens
    
    class TokenStream:
        tokens: list[str]
        index: int
        error: bool

        def __init__(self, tokens: list[str]):
            self.tokens = tokens
            self.index = 0
            self.error = False

        def checkIndex(self) -> bool:
            if (self.index >= len(self.tokens)):
                self.error = True
                return False
            return True

        def read(self) -> str:
            if (not self.checkIndex()):
                return "!"
            
            out = self.tokens[self.index]
            self.index += 1
            return out
        
        def peek(self) -> str:
            if (not self.checkIndex()):
                return "!"
             
            return self.tokens[self.index]
        
        def consume(self):
            if (not self.checkIndex()):
                return
            
            self.index += 1

    @staticmethod
    def loadFromTokenStream(stream: TokenStream, forceObj: bool):
        # it appears the code used in Mewgenics is slightly different from the public github
        # thus forceObj exists allowing files to not start and end with {}

        if (stream.peek() == "{" or forceObj):
            forced = stream.peek() != "{"

            ret: dict[str, Any] = {}

            if (not forced):
                stream.consume()
           
            while (stream.peek() != "}"):
                if (stream.peek().startswith("//")):
                    ret.setdefault("__COMMENTS__", []).append(stream.read().removeprefix("//"))
                    continue

                name = stream.read()
                if (stream.error):
                    if (not forced):
                        GON.on_error("GON ERROR: missing a '}' somewhere")
                        return None
                    else:
                        break

                ret[name] = GON.loadFromTokenStream(stream, False)
                
                if (stream.error):
                    if (not forced):
                        GON.on_error("GON ERROR: missing a '}' somewhere")
                        return None
                    else:
                        break
                    
            if (not forced):
                stream.consume()
            return ret
        
        elif(stream.peek() == "["):
            # using dict so comments can be preserved
            aret: dict[int | str, Any] = {}
            index = 0

            stream.consume()
            while (stream.peek() != "]"):
                if (stream.peek().startswith("//")):
                    aret.setdefault("__COMMENTS__", []).append(stream.read().removeprefix("//"))
                    continue

                aret[index] = GON.loadFromTokenStream(stream, False)
                index += 1

                if (stream.error):
                    GON.on_error("GON ERROR: missing a ']' somewhere")
                    return None
                
            stream.consume()
            return aret
        else:
            while (stream.peek().startswith("//")):
                stream.consume()
                    
            sret: str = stream.read()
            if (stream.error):
                return None

            try:
                return int(sret)
            except ValueError:
                pass

            try:
                return float(sret)
            except ValueError:
                pass

            if (sret == "true"):
                return True
            elif (sret == "false"):
                return False
            
            return sret
    
    @staticmethod
    def loadFromTokens(tokens: list[str]):
        stream = GON.TokenStream(tokens)
        return GON.loadFromTokenStream(stream, True)


import logging
import threading

from . import resource_sync as sync

def gonOnWait(filepath: str):
    logging.debug(f"thread {threading.get_ident()} waiting on parse of {filepath}")

def gonOnWaitEnd(filepath: str):
    logging.debug(f"thread {threading.get_ident()} done waiting on {filepath}")

def gonProduce(filepath: str):
    #logging.debug(f"thread {threading.get_ident()} parsing {filepath}")
   
    with open(filepath, encoding="utf-8-sig") as file:
        content = file.read()

    tokens = GON.tokenize(content)
    return GON.loadFromTokens(tokens)

gonMap = sync.MapSync[Any](gonProduce, gonOnWait, gonOnWaitEnd)

# gons are cached, cause these things get REUSED
def parse_gon(filepath: str):
    return gonMap.get(filepath, filepath)
