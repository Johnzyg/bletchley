Here you will find a brief overview of the tools and libraries provided by Bletchley.  For further details, see the individual tool usage statements, pydoc documentation, and of course the <a href='https://code.google.com/p/bletchley/source/browse/trunk/'>source code</a>.

**Contents**


# Installation #
See: <a href='https://code.google.com/p/bletchley/source/browse/trunk/INSTALL'>INSTALL</a>

# Command Line Tools #

## bletchley-analyze ##

Analyzes samples of encrypted data in an attempt to decode samples to
binary and identify patterns useful in cryptanalysis.  The purpose of
the tool is to provide an cryptanalyst with a variety of information
that is useful in determining how a token is encoded, encrypted and
formatted.
<br />
bletchley-analyze currently performs two primary functions: iterative
encoding detection and ciphertext-only block analysis.  Encrypted tokens
are processed in multiple rounds. Within each round, the following
occurs:
<ul>
<blockquote><li>Token length analysis is performed to attempt to determine possible<br>
ciphertext block sizes, where applicable</li>
<li>The tokens are analyzed for blocks of data that are repeated<br>
throughout any of the tokens</li>
<li>A hexadecimal dump and escaped binary/ascii string is printed for<br>
each token with repeated blocks highlighted</li>
<li>The full set of all known and possible data encodings is<br>
determined<sup>1</sup></li>
<li>An educated guess is made as to the most likely encoding is</li>
<li>All tokens are decoded using the most likely encoding, and then the<br>
process is repeated until no further encodings are detected</li>
</ul></blockquote>

`bletchley-analyze` can read from stdin or from a file.  Tokens are
delimited with newlines.  Various options are provided to give the
analyst control over the block sizes and encoding used during analysis.
See the tool's usage statement for more information.

As an example, several tokens were encrypted using ECB mode and encoded
using base64, and then percent (URL) encoded:
```
zRW5bHxcRYHHqi0nriqOzg%3D%3D
meU8SyxVHE3Hqi0nriqOzg%3D%3D
vTA9eA4hhbFlktsbYI4hIg%3D%3D
meU8SyxVHE1lktsbYI4hIg%3D%3D
```

These tokens were then fed to `bletchley-analyze`:
<img src='https://bletchley.googlecode.com/svn/wiki/images/bletchley-analyze.png' />

1. <i>Bletchley's blobtools module currently supports 36 encoding variants,<br>
including various forms of hexadecimal, base32, base64, and percent<br>
encodings. Try '<code>-e ?</code>' to list them.</i>


## bletchley-encode ##
A simple tool to encode arbitrary data using a specified encoding chain.
See the usage statement for more information.  A quick example:
```
$ echo 'Mallory Is My Friend.' | bletchley-encode -e percent/upper-plus,base64/rfc3548
TWFsbG9yeSBJcyBNeSBGcmllbmQuCg%3D%3D
```

NOTE: The encoding chain is applied from right to left in order to be consistent with other tools.
That is, one can use the same encoding chain ordering for
`bletchley-encode`, `bletchley-decode`, and `bletchley-analyze`.


## bletchley-decode ##
A simple tool to decode data using a specified encoding chain.  See the
usage statement for more information.  A quick example:
```
$ echo 'TWFsbG9yeSBJcyBNeSBGcmllbmQuCg%3D%3D' | bletchley-decode -e percent/upper-plus,base64/rfc3548
Mallory Is My Friend.
```

## bletchley-http2py ##
This script parses an HTTP request (provided via stdin or as a text
file) and generates a Python script that sends (approximately) the same
request.  This is useful when one wants to repeatedly send variations of
a request that was observed to be sent by an application or web
browser.  For more information, see the script's usage statement.

## bletchley-nextrand ##
A simple program which computes the state of a Java Random class
instance given two sequential outputs of
<a href='http://docs.oracle.com/javase/6/docs/api/java/util/Random.html#nextInt()'><code>nextInt()</code></a>.
For more information, see the usage statement.


# Libraries #

Start with '`pydoc3 bletchley`'.  The following provides a brief overview of what each module is for.


## blobtools ##
This module contains the code which handles base analysis of encrypted
token encodings.  It can be used to automatically detect the most likely
encoding variant ("dialect") as well as to quickly encode or decode data
which is wrapped in multiple levels of encodings.


## buffertools ##
This module contains a collection of tools mean to help one manipulate
binary buffers of ciphertext.


## CBC ##
The CBC module contains various tools for attacking CBC encrypted data.
In particular, it contains the POA class which automates padding oracle
attacks.  To use the POA class, one simply needs to implement a function
in Python 3 which submits a request to an oracle and returns True if the
padding check was successful and False otherwise.  See
'`pydoc3 bletchley.CBC.POA`' for more details.


# Support #

Having trouble?  Submit an issue <a href='https://code.google.com/p/bletchley/issues/list'>here</a>, or
ask on the <a href='https://groups.google.com/d/forum/bletchley-devel'>email list</a>.


# Contributing #

We welcome any kind of help with the project, from new tools to bug
fixes and documentation.  You might want to start with our
<a href='https://code.google.com/p/bletchley/source/browse/trunk/doc/TODO'>TODO</a>
list. To submit a patch, just check out a copy of our Subversion
repository, make your changes, and submit the output of `svn diff` to one of the project leaders.