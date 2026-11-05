# Identifier kinds of the Study 2 dotnet-runtime pack

The ontology of this pack is the Study 1 dotnet-runtime ontology with four field kinds added, and the naming rules of Study 1 unchanged. A field declared without an access modifier is private. Kinds not listed below keep their Study 1 meaning.

| Kind | Definition |
|---|---|
| instance_field | A field that is not static and not const, whose accessibility is private, internal, or not stated |
| static_field | A static field, including static readonly, without the ThreadStatic attribute, whose accessibility is private, internal, or not stated |
| threadstatic_field | A static field with the ThreadStatic attribute, whose accessibility is private, internal, or not stated |
| public_field | A public field that is not const, static or not |
| field | A field that is not const and whose accessibility is protected, protected internal, or private protected; no naming rule of this pack applies to it |
| constant | A const field of any accessibility, or a constant local variable |

The kinds are read from the syntax (access modifiers, static, const and the ThreadStatic attribute), so the same definition applies when the kind is taken from metadata and when it is inferred from the code.
