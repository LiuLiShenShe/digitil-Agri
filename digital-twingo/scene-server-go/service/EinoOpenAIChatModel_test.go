package service

import (
	"strings"
	"testing"

	"github.com/cloudwego/eino/schema"
)

// Verifies the finish_reason=tool_calls fix (S5.1): a message that carries tool_calls
// must be preserved (not treated as "empty content" / silently falling to rule fallback).
func TestEinoFromOpenAIMessagePreservesToolCalls(t *testing.T) {
	input := openAIChatMessage{
		Role:    "assistant",
		Content: stringPtr("I will search the catalog."),
		ToolCalls: []openAIToolCall{
			{
				ID:   "call_abc",
				Type: "function",
				Function: openAIFunctionCall{
					Name:      "model.search",
					Arguments: `{"query":"tomato"}`,
				},
			},
		},
	}
	msg := fromOpenAIMessage(input)
	if len(msg.ToolCalls) != 1 {
		t.Fatalf("expected 1 tool call, got %d", len(msg.ToolCalls))
	}
	if msg.ToolCalls[0].Function.Name != "model.search" {
		t.Fatalf("tool name = %q, want model.search", msg.ToolCalls[0].Function.Name)
	}
	if !strings.Contains(msg.Content, "I will search") {
		t.Fatalf("content not preserved: %q", msg.Content)
	}
}

// Verifies toolCallsSummary flattens tool names for downstream routing.
func TestEinoToolCallsSummary(t *testing.T) {
	calls := []schema.ToolCall{
		{ID: "a", Type: "function", Function: schema.FunctionCall{Name: "layout.solve"}},
		{ID: "b", Type: "function", Function: schema.FunctionCall{Name: "object.bind"}},
	}
	sum := toolCallsSummary(calls)
	if !strings.Contains(sum, "layout.solve") || !strings.Contains(sum, "object.bind") {
		t.Fatalf("summary = %q, want both tool names", sum)
	}
}
