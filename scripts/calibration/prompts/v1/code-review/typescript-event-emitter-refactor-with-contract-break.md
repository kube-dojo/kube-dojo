Review this TypeScript refactor diff from an EventEmitter utility. Output one finding per line with:

- file:line citation
- classification: `correctness`, `api`, `concurrency`, or `style`
- concise rationale grounded only in the diff

Unsupported claims count as hallucinations. Do not claim a finding unless the diff
directly supports it.

```diff
diff --git a/src/event_emitter.ts b/src/event_emitter.ts
@@
-export type EventHandler<T = unknown> = (payload: T) => void;
+export type Handler<T = unknown> = (payload: T) => void;
 
 type Listener<T = unknown> = {
-  handler: EventHandler<T>;
+  handler: Handler<T>;
   once: boolean;
 };
 
 export class EventEmitter<T = unknown> {
-  private readonly listeners = new Map<string, Listener<T>[]>();
+  private readonly listeners = new Map<string, Listener<T>[]>();
 
-  on(event: string, handler: EventHandler<T>): () => void {
-    const listeners = this.listeners.get(event) ?? [];
-    listeners.push({ handler, once: false });
-    this.listeners.set(event, listeners);
-    return () => this.off(event, handler);
-  }
+  on(event: string, handler: Handler<T>): () => void {
+    const listeners = this.listeners.get(event) ?? [];
+    listeners.push({ handler, once: false });
+    this.listeners.set(event, listeners);
+    return () => this.off(event, handler);
+  }
 
-  once(event: string, handler: EventHandler<T>): () => void {
-    const listeners = this.listeners.get(event) ?? [];
-    listeners.push({ handler, once: true });
-    this.listeners.set(event, listeners);
-    return () => this.off(event, handler);
-  }
+  once(event: string, handler: Handler<T>): () => void {
+    const listeners = this.listeners.get(event) ?? [];
+    const entry: Listener<T> = { handler, once: true };
+    entry.handler = this.subscribeOnce(event, entry);
+    listeners.push(entry);
+    this.listeners.set(event, listeners);
+    return () => this.off(event, entry.handler);
+  }
+
+  private subscribeOnce(event: string, entry: Listener<T>): Handler<T> {
+    return (payload: T) => {
+      const listeners = this.listeners.get(event) ?? [];
+      const index = listeners.indexOf(entry);
+      if (index >= 0) {
+        listeners.splice(index, 1);
+      }
+      entry.handler(payload);
+    };
+  }
 
   emit(event: string, payload: T): void {
     const listeners = this.listeners.get(event);
     if (!listeners) {
       return;
     }
-    for (const listener of [...listeners]) {
-      try {
-        listener.handler(payload);
-      } catch (error) {
-        console.error(`EventEmitter handler for ${event} failed`, error);
-      } finally {
-        if (listener.once) {
-          this.off(event, listener.handler);
-        }
-      }
-    }
+    for (let i = 0; i < listeners.length; i++) {
+      listeners[i].handler(payload);
+    }
+  }
+
+  private off(event: string, handler: Handler<T>): void {
+    const listeners = this.listeners.get(event);
+    if (!listeners) {
+      return;
+    }
+    const next = listeners.filter((listener) => listener.handler !== handler);
+    if (next.length === 0) {
+      this.listeners.delete(event);
+    } else {
+      this.listeners.set(event, next);
+    }
   }
 }
diff --git a/tests/event_emitter.test.ts b/tests/event_emitter.test.ts
@@
-import { EventEmitter, EventHandler } from "../src/event_emitter";
+import { EventEmitter, Handler } from "../src/event_emitter";
 import { describe, expect, it } from "vitest";
 
 describe("EventEmitter", () => {
   it("calls once handler only once", () => {
-    const emitter = new EventEmitter<string>();
-    const values: string[] = [];
-    const handler: EventHandler<string> = (value) => values.push(value);
+    const emitter = new EventEmitter<string>();
+    const values: string[] = [];
+    const handler: Handler<string> = (value) => values.push(value);
 
     emitter.once("ready", handler);
     emitter.emit("ready", "a");
     emitter.emit("ready", "b");
 
     expect(values).toEqual(["a"]);
   });
 
-  it("supports re-subscribing from inside a once handler", () => {
-    const emitter = new EventEmitter<number>();
-    const values: number[] = [];
-
-    emitter.once("tick", (value) => {
-      values.push(value);
-      emitter.once("tick", () => values.push(value + 1));
-    });
-
-    emitter.emit("tick", 1);
-    emitter.emit("tick", 2);
-    expect(values).toEqual([1, 2]);
-  });
+  it("can surface handler failures from emit()", () => {
+    const emitter = new EventEmitter<number>();
+    const handler: Handler<number> = () => {
+      throw new Error("handler failure");
+    };
+    const values: number[] = [1];
+
+    emitter.on("tick", (value) => values.push(value));
+    emitter.on("tick", handler);
+    expect(() => emitter.emit("tick", 2)).toThrow("handler failure");
+    expect(values).toEqual([1, 2]);
+  });
 });
```
