// Lista curada de modelos por proveedor. Mantenida a mano: cuando salga un
// modelo nuevo basta con añadirlo aquí (sin regenerar la gramática). El
// Validator usa esta lista para marcar modelos inválidos para el provider, y
// el CompletionProvider la usa para autocompletar.
//
// Fuentes consultadas (revisar periódicamente):
//   openai    → https://developers.openai.com/api/docs/models/all
//   anthropic → https://platform.claude.com/docs/en/about-claude/models/overview
//   google    → https://ai.google.dev/gemini-api/docs/models
//   ollama    → https://ollama.com/library
export const PROVIDERS = ['openai', 'anthropic', 'google', 'ollama'] as const;
export type Provider = typeof PROVIDERS[number];

export const MODELS: Record<Provider, readonly string[]> = {
    openai: [
        'gpt-5.4',
        'gpt-5.4-pro',
        'gpt-5.4-mini',
        'gpt-5.4-nano',
        'gpt-5.2-pro',
        'gpt-5.2',
        'gpt-5.1',
        'gpt-5-pro',
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano',
        'gpt-4.1',
        'gpt-4.1-mini',
        'gpt-4.1-nano',
        'gpt-4o',
        'gpt-4o-mini',
        'o3-pro',
        'o3',
        'o4-mini',
        'o3-mini',
        'o1-pro',
        'o1'
    ],
    anthropic: [
        'claude-opus-4-7',
        'claude-sonnet-4-6',
        'claude-haiku-4-5',
        'claude-opus-4-6',
        'claude-sonnet-4-5',
        'claude-opus-4-5',
        'claude-opus-4-1'
    ],
    google: [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-3.1-pro-preview',
        'gemini-3-flash-preview',
        'gemini-3.1-flash-lite-preview',
        'gemini-flash-latest'
    ],
    ollama: [
        'llama3.3',
        'llama3.2',
        'llama3.1',
        'qwen3',
        'qwen2.5',
        'deepseek-r1',
        'mistral',
        'gemma2',
        'phi3'
    ]
};

export function isKnownProvider(value: string): value is Provider {
    return (PROVIDERS as readonly string[]).includes(value);
}

export function modelsFor(provider: string): readonly string[] {
    return isKnownProvider(provider) ? MODELS[provider] : [];
}
