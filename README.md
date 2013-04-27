Clojure-inspired multimethods for Python
========================================
Reasonably performant multimethods based on Clojure's multimethod code.

The main code was initially transliterated from Clojure's code (MultiFn.java) but
has been simplified somewhat.  Unlike Clojure, there is no global hierarchy and
you must instead explicitly create hierarchies.  Hierarchies in this library also
only support single inheritance (as opposed to Clojure's multiple inheritance).
The hand-wavy reason for this simplification is that giving the programmer the
ability use multiple hierarchies obviates the need to have multiple inheritance
but I am willing to be convinced otherwise with a good argument.

Licensing issues
----------------
As I originally transliterated code from Clojure's source tree, the transliterated
code is covered by Clojure's licence, the EPL.  I plan on asking Rich Hickey for
permission to relicense this code under the BSD.

Acknowledgements
================
Rich Hickey for his simple and yet amazingly powerful code.
Heiko Wundram for the read-write lock code.
