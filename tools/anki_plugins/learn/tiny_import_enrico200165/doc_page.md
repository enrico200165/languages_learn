**Didactical**, Anki already has a (far more) powerful import functionality.  
It's a first plugin written to start learning.  

Imports lines from a text file.  
If no note with the read value exists creates a new note with that value, embedded in the marker, in the chosen deck, model and field. 

The value is suffixed and prefixed by a marker set in the code by  

```
MARKER_PREFIX = "###-must-fill: "
MARKER_SUFFIX = ""  
```
So if "myVal" does not exist in the chosen deck, model and field a new note will be created with value "###-must-fill: myVal"  
Obviously the check for existence filters out the marker if present.

The text file to import, the target deck, model and field are chosen by the user on the GUI.

The only practical utility I can see is the fact that it adds a marker to easily identify new cards to be filled   
(but I think this could be done with the normal import using an additional field set to a marker/flag value, a "flag", "star-ring" the note Etc.  
so no practical utility for this plugin except didactic or, maybe, for beginner users)