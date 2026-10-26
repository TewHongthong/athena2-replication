import com.sun.source.tree.*;
import com.sun.source.util.*;
import javax.lang.model.element.*;
import javax.tools.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Java front end for the scope-aware check: javac parse + attribution, then every declaration and every
 *  identifier / member-select occurrence with the element it resolves to. Reads file paths (one per line) from
 *  stdin, prints one JSON object per file. */
public class ScopeDump {
    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 32) b.append(String.format("\\u%04x", (int) c));
            else b.append(c);
        }
        return b.append('"').toString();
    }

    public static void main(String[] a) throws Exception {
        JavaCompiler jc = ToolProvider.getSystemJavaCompiler();
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = in.readLine()) != null) {
            if (line.isBlank()) continue;
            System.out.println(dump(jc, line.trim()));
            System.out.flush();
        }
    }

    static String dump(JavaCompiler jc, String file) throws Exception {
        DiagnosticCollector<JavaFileObject> dc = new DiagnosticCollector<>();
        StandardJavaFileManager fm = jc.getStandardFileManager(dc, null, StandardCharsets.UTF_8);
        JavacTask task = (JavacTask) jc.getTask(null, fm, dc, List.of("-proc:none", "-Xlint:none", "-d",
                Files.createTempDirectory("sd").toString()), null, fm.getJavaFileObjects(file));
        Iterable<? extends CompilationUnitTree> units = task.parse();
        task.analyze();
        Trees trees = Trees.instance(task);
        SourcePositions sp = trees.getSourcePositions();
        StringBuilder out = new StringBuilder("{\"file\":" + q(file) + ",\"errors\":[");
        boolean first = true;
        for (Diagnostic<? extends JavaFileObject> d : dc.getDiagnostics()) {
            if (d.getKind() != Diagnostic.Kind.ERROR) continue;
            out.append(first ? "" : ",").append(q(d.getLineNumber() + ": " + d.getMessage(Locale.ROOT)));
            first = false;
        }
        out.append("],\"decls\":[");
        Map<Element, Long> declPos = new HashMap<>();
        List<String> decls = new ArrayList<>();
        List<String> occ = new ArrayList<>();
        for (CompilationUnitTree cu : units) {
            // pass 1: declarations (element -> start position) with their scope path
            new TreePathScanner<Void, Deque<String>>() {
                void decl(Tree t, String name, Deque<String> sc) {
                    Element e = trees.getElement(getCurrentPath());
                    long p = sp.getStartPosition(cu, t);
                    if (e != null) declPos.put(e, p);
                    String kind = e != null ? e.getKind().toString() : t.getKind().toString();
                    decls.add("{\"name\":" + q(name) + ",\"kind\":" + q(kind) + ",\"pos\":" + p + ",\"scope\":" + scope(sc) + "}");
                }
                String scope(Deque<String> sc) {
                    StringBuilder b = new StringBuilder("[");
                    Iterator<String> it = sc.descendingIterator();
                    boolean f = true;
                    while (it.hasNext()) { b.append(f ? "" : ",").append(it.next()); f = false; }
                    return b.append("]").toString();
                }
                Void push(Tree t, String kind, Deque<String> sc, Runnable r) {
                    sc.push("[" + q(kind) + "," + sp.getStartPosition(cu, t) + "]");
                    r.run();
                    sc.pop();
                    return null;
                }
                @Override public Void visitClass(ClassTree t, Deque<String> sc) {
                    decl(t, t.getSimpleName().toString(), sc);
                    return push(t, "class", sc, () -> super.visitClass(t, sc));
                }
                @Override public Void visitMethod(MethodTree t, Deque<String> sc) {
                    decl(t, t.getName().toString(), sc);
                    return push(t, "method", sc, () -> super.visitMethod(t, sc));
                }
                @Override public Void visitVariable(VariableTree t, Deque<String> sc) {
                    decl(t, t.getName().toString(), sc);
                    return super.visitVariable(t, sc);
                }
                @Override public Void visitBlock(BlockTree t, Deque<String> sc) { return push(t, "block", sc, () -> super.visitBlock(t, sc)); }
                @Override public Void visitForLoop(ForLoopTree t, Deque<String> sc) { return push(t, "for", sc, () -> super.visitForLoop(t, sc)); }
                @Override public Void visitEnhancedForLoop(EnhancedForLoopTree t, Deque<String> sc) { return push(t, "for", sc, () -> super.visitEnhancedForLoop(t, sc)); }
                @Override public Void visitCatch(CatchTree t, Deque<String> sc) { return push(t, "catch", sc, () -> super.visitCatch(t, sc)); }
                @Override public Void visitTry(TryTree t, Deque<String> sc) { return push(t, "try", sc, () -> super.visitTry(t, sc)); }
                @Override public Void visitLambdaExpression(LambdaExpressionTree t, Deque<String> sc) { return push(t, "lambda", sc, () -> super.visitLambdaExpression(t, sc)); }
                @Override public Void visitSwitch(SwitchTree t, Deque<String> sc) { return push(t, "switch", sc, () -> super.visitSwitch(t, sc)); }
            }.scan(cu, new ArrayDeque<>(List.of("[\"CU\",0]")));
            // pass 2: references
            new TreePathScanner<Void, Deque<String>>() {
                String key(Element e) {
                    if (e == null) return "[\"none\"]";
                    Long p = declPos.get(e);
                    if (p != null) return "[\"src\"," + q(e.getKind().toString()) + "," + p + "]";
                    Element enc = e.getEnclosingElement();
                    return "[\"ext\"," + q(e.getKind().toString()) + "," + q((enc != null ? enc.toString() + "." : "") + e.toString()) + "]";
                }
                void ref(Tree t, long pos, String name, boolean simple, Deque<String> sc) {
                    Element e = trees.getElement(getCurrentPath());
                    boolean ext = e == null || !declPos.containsKey(e);
                    occ.add("{\"pos\":" + pos + ",\"name\":" + q(name) + ",\"key\":" + key(e) + ",\"simple\":" + simple
                            + ",\"ext\":" + ext + ",\"scope\":" + scope(sc) + "}");
                }
                String scope(Deque<String> sc) {
                    StringBuilder b = new StringBuilder("[");
                    Iterator<String> it = sc.descendingIterator();
                    boolean f = true;
                    while (it.hasNext()) { b.append(f ? "" : ",").append(it.next()); f = false; }
                    return b.append("]").toString();
                }
                Void push(Tree t, String kind, Deque<String> sc, Runnable r) {
                    sc.push("[" + q(kind) + "," + sp.getStartPosition(cu, t) + "]");
                    r.run();
                    sc.pop();
                    return null;
                }
                @Override public Void visitIdentifier(IdentifierTree t, Deque<String> sc) {
                    ref(t, sp.getStartPosition(cu, t), t.getName().toString(), true, sc);
                    return super.visitIdentifier(t, sc);
                }
                @Override public Void visitMemberSelect(MemberSelectTree t, Deque<String> sc) {
                    String n = t.getIdentifier().toString();
                    ref(t, sp.getEndPosition(cu, t) - n.length(), n, false, sc);
                    return super.visitMemberSelect(t, sc);
                }
                @Override public Void visitClass(ClassTree t, Deque<String> sc) { return push(t, "class", sc, () -> super.visitClass(t, sc)); }
                @Override public Void visitMethod(MethodTree t, Deque<String> sc) { return push(t, "method", sc, () -> super.visitMethod(t, sc)); }
                @Override public Void visitBlock(BlockTree t, Deque<String> sc) { return push(t, "block", sc, () -> super.visitBlock(t, sc)); }
                @Override public Void visitForLoop(ForLoopTree t, Deque<String> sc) { return push(t, "for", sc, () -> super.visitForLoop(t, sc)); }
                @Override public Void visitEnhancedForLoop(EnhancedForLoopTree t, Deque<String> sc) { return push(t, "for", sc, () -> super.visitEnhancedForLoop(t, sc)); }
                @Override public Void visitCatch(CatchTree t, Deque<String> sc) { return push(t, "catch", sc, () -> super.visitCatch(t, sc)); }
                @Override public Void visitTry(TryTree t, Deque<String> sc) { return push(t, "try", sc, () -> super.visitTry(t, sc)); }
                @Override public Void visitLambdaExpression(LambdaExpressionTree t, Deque<String> sc) { return push(t, "lambda", sc, () -> super.visitLambdaExpression(t, sc)); }
                @Override public Void visitSwitch(SwitchTree t, Deque<String> sc) { return push(t, "switch", sc, () -> super.visitSwitch(t, sc)); }
            }.scan(cu, new ArrayDeque<>(List.of("[\"CU\",0]")));
        }
        out.append(String.join(",", decls)).append("],\"occ\":[").append(String.join(",", occ)).append("]}");
        fm.close();
        return out.toString();
    }
}
