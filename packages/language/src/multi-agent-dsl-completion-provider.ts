import type { MaybePromise } from 'langium';
import { GrammarAST } from 'langium';
import { CompletionAcceptor, CompletionContext, DefaultCompletionProvider, NextFeature } from 'langium/lsp';
import { CompletionItemKind } from 'vscode-languageserver';
import { isAgent } from './generated/ast.js';
import { modelsFor } from './models.js';

export class MultiAgentDslCompletionProvider extends DefaultCompletionProvider {

    protected override completionFor(
        context: CompletionContext,
        next: NextFeature,
        acceptor: CompletionAcceptor
    ): MaybePromise<void> {
        const feature = next.feature;
        if (
            GrammarAST.isAssignment(feature) &&
            feature.feature === 'model' &&
            context.node && isAgent(context.node)
        ) {
            for (const model of modelsFor(context.node.provider)) {
                acceptor(context, {
                    label: model,
                    kind: CompletionItemKind.Value,
                    insertText: `"${model}"`,
                    detail: `modelo de ${context.node.provider}`
                });
            }
            return;
        }
        return super.completionFor(context, next, acceptor);
    }
}
