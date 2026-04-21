import type { ValidationAcceptor, ValidationChecks } from 'langium';
import type { Agent, MultiAgentDslAstType } from './generated/ast.js';
import type { MultiAgentDslServices } from './multi-agent-dsl-module.js';
import { modelsFor } from './models.js';

export function registerValidationChecks(services: MultiAgentDslServices) {
    const registry = services.validation.ValidationRegistry;
    const validator = services.validation.MultiAgentDslValidator;
    const checks: ValidationChecks<MultiAgentDslAstType> = {
        // TODO: restricciones de bien-formedness
        Agent: validator.checkAgentModel
    };
    registry.register(checks, validator);
}

export class MultiAgentDslValidator {

    checkAgentModel(agent: Agent, accept: ValidationAcceptor): void {
        const allowed = modelsFor(agent.provider);
        if (allowed.length === 0 || allowed.includes(agent.model)) {
            return;
        }
        accept(
            'error',
            `Modelo "${agent.model}" no válido para provider "${agent.provider}". Modelos válidos: ${allowed.join(', ')}.`,
            { node: agent, property: 'model' }
        );
    }
}
