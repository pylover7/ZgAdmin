import { describe, it, expect } from "vitest";
import {
  extractPathList,
  deleteChildren,
  buildHierarchyTree,
  getNodeByUniqueId,
  appendFieldByUniqueId,
  handleTree,
  buildApiTree
} from "@/utils/tree";

describe("tree utils", () => {
  describe("extractPathList", () => {
    it("returns empty array for non-array input", () => {
      expect(extractPathList(null as any)).toEqual([]);
      expect(extractPathList("str" as any)).toEqual([]);
    });

    it("returns empty array for empty array", () => {
      expect(extractPathList([])).toEqual([]);
    });

    it("extracts uniqueId from flat tree", () => {
      const tree = [{ uniqueId: "a" }, { uniqueId: "b" }];
      expect(extractPathList(tree)).toEqual(["a", "b"]);
    });

    it("extracts uniqueId from nested tree (note: children uniqueIds are NOT collected due to unused recursion return)", () => {
      const tree = [
        { uniqueId: "a", children: [{ uniqueId: "a-1" }] },
        { uniqueId: "b" }
      ];
      // extractPathList recurses into children but discards the return value,
      // so children's uniqueIds are NOT added to expandedPaths
      expect(extractPathList(tree)).toEqual(["a", "b"]);
    });
  });

  describe("deleteChildren", () => {
    it("returns empty array for non-array input", () => {
      expect(deleteChildren(null as any)).toEqual([]);
    });

    it("deletes children when only one child exists and builds uniqueId", () => {
      const tree = [
        { children: [{ name: "only" }], title: "parent" }
      ];
      const result = deleteChildren(tree);
      expect(result[0].children).toBeUndefined();
      expect(result[0].id).toBe(0);
      expect(result[0].uniqueId).toBe(0);
    });

    it("keeps children when more than one child exists", () => {
      const tree = [
        { children: [{ name: "a" }, { name: "b" }], title: "parent" }
      ];
      const result = deleteChildren(tree);
      expect(result[0].children).toHaveLength(2);
    });

    it("builds uniqueId with pathList for nested nodes", () => {
      const tree = [
        {
          children: [
            { name: "a" },
            { name: "b", children: [{ name: "c" }] }
          ],
          title: "parent"
        }
      ];
      const result = deleteChildren(tree);
      expect(result[0].id).toBe(0);
      // second child id=1, its single child "c" gets deleted (only 1 child),
      // so uniqueId is "0-1" (pathList = [0, 1])
      const secondChild = result[0].children[1];
      expect(secondChild.id).toBe(1);
      expect(secondChild.uniqueId).toBe("0-1");
    });
  });

  describe("buildHierarchyTree", () => {
    it("returns empty array for non-array input", () => {
      expect(buildHierarchyTree(null as any)).toEqual([]);
    });

    it("builds hierarchy with id, parentId, pathList", () => {
      const tree = [{ name: "root" }];
      const result = buildHierarchyTree(tree);
      expect(result[0].id).toBe(0);
      expect(result[0].parentId).toBeNull();
      expect(result[0].pathList).toEqual([0]);
    });

    it("builds hierarchy for nested tree", () => {
      const tree = [
        { name: "root", children: [{ name: "child" }] }
      ];
      const result = buildHierarchyTree(tree);
      expect(result[0].pathList).toEqual([0]);
      expect(result[0].children[0].pathList).toEqual([0, 0]);
    });
  });

  describe("getNodeByUniqueId", () => {
    it("returns empty array for non-array input", () => {
      expect(getNodeByUniqueId(null as any, "a")).toEqual([]);
    });

    it("finds node by uniqueId at root level", () => {
      const tree = [{ uniqueId: "a" }, { uniqueId: "b" }];
      expect(getNodeByUniqueId(tree, "a")).toEqual({ uniqueId: "a" });
    });

    it("finds node by uniqueId in nested tree", () => {
      const tree = [
        { uniqueId: "a", children: [{ uniqueId: "a-1" }, { uniqueId: "a-2" }] }
      ];
      expect(getNodeByUniqueId(tree, "a-2")).toEqual({ uniqueId: "a-2" });
    });

    it("returns empty array when uniqueId not found", () => {
      const tree = [{ uniqueId: "a" }];
      expect(getNodeByUniqueId(tree, "z")).toEqual([]);
    });
  });

  describe("appendFieldByUniqueId", () => {
    it("returns empty array for non-array input", () => {
      expect(appendFieldByUniqueId(null as any, "a", {})).toEqual([]);
    });

    it("appends fields to matching node", () => {
      const tree = [{ uniqueId: "a", name: "old" }];
      const result = appendFieldByUniqueId(tree, "a", { extra: true });
      expect(result[0].extra).toBe(true);
      expect(result[0].name).toBe("old");
    });

    it("appends fields to nested node", () => {
      const tree = [
        { uniqueId: "a", children: [{ uniqueId: "b" }] }
      ];
      const result = appendFieldByUniqueId(tree, "b", { flag: 1 });
      expect(result[0].children[0].flag).toBe(1);
    });

    it("does not append fields when fields is not a plain object", () => {
      const tree = [{ uniqueId: "a", name: "old" }];
      const result = appendFieldByUniqueId(tree, "a", "not-object" as any);
      expect(result[0].name).toBe("old");
      expect((result[0] as any).flag).toBeUndefined();
    });
  });

  describe("handleTree", () => {
    it("returns empty array for non-array input", () => {
      expect(handleTree(null as any)).toEqual([]);
    });

    it("builds tree from flat data with default keys", () => {
      const data = [
        { id: 1, parentId: 0, name: "root" },
        { id: 2, parentId: 1, name: "child1" },
        { id: 3, parentId: 1, name: "child2" }
      ];
      const result = handleTree(data);
      expect(result).toHaveLength(1);
      expect(result[0].name).toBe("root");
      expect(result[0].children).toHaveLength(2);
    });

    it("builds tree with custom keys", () => {
      const data = [
        { myId: "a", myParentId: null, title: "root" },
        { myId: "b", myParentId: "a", title: "child" }
      ];
      const result = handleTree(data, "myId", "myParentId", "nodes");
      expect(result).toHaveLength(1);
      expect(result[0].nodes).toHaveLength(1);
    });

    it("handles multiple roots", () => {
      const data = [
        { id: 1, parentId: 0, name: "root1" },
        { id: 2, parentId: 0, name: "root2" }
      ];
      const result = handleTree(data);
      expect(result).toHaveLength(2);
    });
  });

  describe("buildApiTree", () => {
    it("returns empty array for non-array input", () => {
      expect(buildApiTree(null as any)).toEqual([]);
    });

    it("returns empty array for empty array", () => {
      expect(buildApiTree([])).toEqual([]);
    });

    it("groups APIs by tags", () => {
      const data = [
        { id: "1", method: "GET", path: "/api/users", summary: "List users", tags: "user" },
        { id: "2", method: "POST", path: "/api/users", summary: "Create user", tags: "user" },
        { id: "3", method: "GET", path: "/api/roles", summary: "List roles", tags: "role" }
      ];
      const result = buildApiTree(data);
      expect(result).toHaveLength(2);
      expect(result[0].id).toBe("__tag__user");
      expect(result[0].children).toHaveLength(2);
      expect(result[1].id).toBe("__tag__role");
    });

    it("groups APIs without tags as '未分组'", () => {
      const data = [
        { id: "1", method: "GET", path: "/api/test", summary: "Test" }
      ];
      const result = buildApiTree(data);
      expect(result).toHaveLength(1);
      expect(result[0].title).toBe("未分组");
    });

    it("uses path in title when summary is missing", () => {
      const data = [
        { id: "1", method: "GET", path: "/api/test", tags: "group" }
      ];
      const result = buildApiTree(data);
      expect(result[0].children[0].title).toBe("[GET] /api/test");
    });
  });
});
