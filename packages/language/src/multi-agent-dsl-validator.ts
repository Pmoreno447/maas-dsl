import type { ValidationAcceptor, ValidationChecks } from 'langium';
import type { MultiAgentDslAstType, Person } from './generated/ast.js';
import type { MultiAgentDslServices } from './multi-agent-dsl-module.js';

/**
 * Register custom validation checks.
 */
export function registerValidationChecks(services: MultiAgentDslServices) {
    const registry = services.validation.ValidationRegistry;
    const validator = services.validation.MultiAgentDslValidator;
    const checks: ValidationChecks<MultiAgentDslAstType> = {
        Person: validator.checkPersonStartsWithCapital
    };
    registry.register(checks, validator);
}

/**
 * Implementation of custom validations.
 */
export class MultiAgentDslValidator {

    checkPersonStartsWithCapital(person: Person, accept: ValidationAcceptor): void {
        if (person.name) {
            const firstChar = person.name.substring(0, 1);
            if (firstChar.toUpperCase() !== firstChar) {
                accept('warning', 'Person name should start with a capital.', { node: person, property: 'name' });
            }
        }
    }

}
