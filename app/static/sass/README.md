In our SASS, classes are prefixed by one of 3 letters: `.b-classname`,
`.e-classname` or `.m-classname`.

* `.b-classname` are blocks that exist in the global scope.

* `.e-classname` only exists inside a `.b-classname`. This prevents most
  of the style conflicts and makes naming much easier. The `.e-` stands 
  for "element".

* `.m-classname` stands for "modifier", and they only exist when
  coupled with another `.b-` or `.e-`. 
