Clojure-inspired multimethods for Python
========================================
Reasonably performant multimethods based on Clojure's multimethod code.

The main code was initially transliterated from Clojure's code (MultiFn.java) but
has been simplified somewhat.

About performance
-----------------
A big issue with many of the multimethod implementations available for Python today,
is that they seldom focus on performance.  This implementation uses the age-old
method signature cache trick (the implementation is pretty much that used in Clojure)
to quickly find methods matching the argument signature.  The cache is cleared when
the hierarchy is changed or when a new method implementation is added.

Obviously, there is an initial speed hit before the implementation corresponding to
an argument signature is cached.  Constantly adding or removing method implementations
or changing the relationship hierarchy is a sure-fire way to have abysmal performance.

Megamorphic methods - that is, methods in which argument types are expected to vary
greatly, are likely going to cause problems with the current implementation.  At least
if they dispatch on multiple arguments.  Suppose that we have a method with three
polymorphic arguments.  Each argument can assume 50 types (perhaps representing HTML
tags or some such).  Then your cache will eventually contain 50x50x50=125000 entries.

Licensing issues
----------------
As I originally transliterated code from Clojure's source tree, the transliterated
code is covered by Clojure's licence, the EPL.  I plan on asking Rich Hickey for
permission to relicense this code under the BSD.

Acknowledgements
================
Rich Hickey for his simple and yet amazingly powerful code.
Heiko Wundram for the read-write lock code.
