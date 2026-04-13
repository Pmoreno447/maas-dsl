import { AstUtils, DefaultScopeProvider, ReferenceInfo, Scope, MapScope } from 'langium';
import { isLLMMultiAgentSystem, type LLMMultiAgentSystem } from './generated/ast.js';

export class MultiAgentDslScopeProvider extends DefaultScopeProvider {

    override getScope(context: ReferenceInfo): Scope {
        // Para las referencias de Agent.stateContext y Agent.stateUpdate a Attribute,
        // buscamos los atributos dentro del Environment del sistema.
        if (context.property === 'stateContext' || context.property === 'stateUpdate') {
            const system = AstUtils.getContainerOfType(context.container, isLLMMultiAgentSystem) as LLMMultiAgentSystem | undefined;
            if (system?.envirement) {
                const descriptions = system.envirement.attributes.map(attr =>
                    this.descriptions.createDescription(attr, attr.name)
                );
                return new MapScope(descriptions);
            }
        }
        return super.getScope(context);
    }
}
