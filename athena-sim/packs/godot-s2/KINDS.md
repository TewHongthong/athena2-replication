# Identifier kinds of the Study 2 Godot pack

The ontology of this pack is the Study 1 Godot ontology with two kinds added, input_parameter and output_parameter, and the naming rules of Study 1 unchanged. Kinds not listed below keep their Study 1 meaning.

| Kind | From metadata (benchmark) | Inferred from the code |
|---|---|---|
| input_parameter | A parameter of a method (a function declared in, or defined for, a class, struct or union) whose name in the original code starts with p_ | A method parameter whose type is not a reference or a pointer to a type that is not const |
| output_parameter | A method parameter whose name in the original code starts with r_ | A method parameter whose type is a reference or a pointer to a type that is not const |
| parameter | Every parameter of a free function, and a method parameter whose name in the original code starts with neither p_ nor r_ | A parameter of a free function |

A parameter of kind parameter is checked for snake_case only and is not an injection target of Study 2.
