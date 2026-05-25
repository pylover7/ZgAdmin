import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockUseEventListener } = vi.hoisted(() => ({
  mockUseEventListener: vi.fn()
}));

vi.mock("@vueuse/core", () => ({
  useEventListener: mockUseEventListener
}));

describe("preventDefault", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("addPreventDefault registers 4 event listeners", async () => {
    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();
    expect(mockUseEventListener).toHaveBeenCalledTimes(4);
  });

  it("keydown listener prevents F12", async () => {
    const listeners: Array<{ event: string; handler: Function }> = [];
    mockUseEventListener.mockImplementation((_target: any, event: string, handler: Function) => {
      listeners.push({ event, handler });
    });

    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();

    const keydownListener = listeners.find(l => l.event === "keydown");
    expect(keydownListener).toBeDefined();

    const mockEvent = { key: "F12", preventDefault: vi.fn() };
    keydownListener!.handler(mockEvent);
    expect(mockEvent.preventDefault).toHaveBeenCalled();
  });

  it("keydown listener does not prevent non-F12 keys", async () => {
    const listeners: Array<{ event: string; handler: Function }> = [];
    mockUseEventListener.mockImplementation((_target: any, event: string, handler: Function) => {
      listeners.push({ event, handler });
    });

    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();

    const keydownListener = listeners.find(l => l.event === "keydown");
    const mockEvent = { key: "Enter", preventDefault: vi.fn() };
    keydownListener!.handler(mockEvent);
    expect(mockEvent.preventDefault).not.toHaveBeenCalled();
  });

  it("contextmenu listener prevents default", async () => {
    const listeners: Array<{ event: string; handler: Function }> = [];
    mockUseEventListener.mockImplementation((_target: any, event: string, handler: Function) => {
      listeners.push({ event, handler });
    });

    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();

    const contextmenuListener = listeners.find(l => l.event === "contextmenu");
    expect(contextmenuListener).toBeDefined();

    const mockEvent = { preventDefault: vi.fn() };
    contextmenuListener!.handler(mockEvent);
    expect(mockEvent.preventDefault).toHaveBeenCalled();
  });

  it("selectstart listener prevents default", async () => {
    const listeners: Array<{ event: string; handler: Function }> = [];
    mockUseEventListener.mockImplementation((_target: any, event: string, handler: Function) => {
      listeners.push({ event, handler });
    });

    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();

    const selectstartListener = listeners.find(l => l.event === "selectstart");
    expect(selectstartListener).toBeDefined();

    const mockEvent = { preventDefault: vi.fn() };
    selectstartListener!.handler(mockEvent);
    expect(mockEvent.preventDefault).toHaveBeenCalled();
  });

  it("dragstart listener is registered", async () => {
    const listeners: Array<{ event: string; handler: Function }> = [];
    mockUseEventListener.mockImplementation((_target: any, event: string, handler: Function) => {
      listeners.push({ event, handler });
    });

    const { addPreventDefault } = await import("@/utils/preventDefault");
    addPreventDefault();

    const dragstartListener = listeners.find(l => l.event === "dragstart");
    expect(dragstartListener).toBeDefined();
    // The dragstart handler checks isImgElement(ev?.target) && ev.preventDefault()
    // isImgElement uses instanceof HTMLImageElement or tagName check
    // Since our mock target is a plain object, it won't match HTMLImageElement
    // and tagName.toLowerCase() would need "img" for the check
  });
});
