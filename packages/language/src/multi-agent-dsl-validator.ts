import type { ValidationChecks } from 'langium';
import type { MultiAgentDslAstType } from './generated/ast.js';
import type { MultiAgentDslServices } from './multi-agent-dsl-module.js';

export function registerValidationChecks(services: MultiAgentDslServices) {
    const registry = services.validation.ValidationRegistry;
    const validator = services.validation.MultiAgentDslValidator;
    const checks: ValidationChecks<MultiAgentDslAstType> = {
        // TODO: restricciones de bien-formedness
    };
    registry.register(checks, validator);
}

export class MultiAgentDslValidator {

}
