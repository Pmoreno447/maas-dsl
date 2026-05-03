grammar MultiAgentDsl

entry LLMMultiAgentSystem:
    '{'
        envirement=Environment
        profiles+=Profile*
        tools+=(PythonTool | MCPServer )*
        agents+=Agent*
        communicationStructures+=(Layered | SharedMessagePool | Centralized | Decentralized)*
        transitions+=CommTransition*
    '}';

// Toda esta sección define la parte del entorno en que se encuentra el MAAS.
// GameRule: Debe revisarse

AttributeType returns string:
    'int' | 'string' | 'boolean';

type PersistenceValue = InMemorySaver | PostgreSaver | MongoDBSaver;

InMemorySaver:
    {infer InMemorySaver} 'inMemorySave';

PostgreSaver:
    {infer PostgreSaver} 'Postgre';

MongoDBSaver:
    {infer MongoDBSaver} 'MongoDB';

Environment:
    'environment' name = ID '{'
        gamerules+=GameRule*
        attributes+=Attribute*
        messages=(Trim | Mix | None | Summarize)
        'persistence' persistence=( InMemorySaver | PostgreSaver | MongoDBSaver)
    '}';

GameRule:
    'gamerule' id = ID 'description' description = STRING;

// TODO: soporte para literales en atributos. Pendiente de implementar en el generador
// (stateGenerator.ts y agentsGenerator.ts ignoran actualmente este campo).
// fragment Literal:
//     'literal' '{'
//         ('value' value+=STRING)+
//     '}';

Attribute:
    'attribute' name = ID 'type' type = AttributeType 'description' description = STRING /* (Literal)? */;

type Message = Trim | Mix | None | Summarize;

Trim:
    'trim' '{' 
        'maxMessages' maxMessages = INT
    '}';

Mix:
    'mix' '{'
        'maxToken' maxToken = INT 
        'maxMessages' maxMessages = INT
        ProviderModel
    '}';

Summarize:
    'summarize' '{' 
        'maxToken' maxToken = INT
        ProviderModel
    '}';

None:
    {infer None} 'none';


// A partir de ahora, se define todo lo relacionado con los agentes individuales:
// El proveedor es estático (impacta a la generación: API keys, imports). El
// modelo es un STRING libre validado contra una lista curada por proveedor en
// models.json (ver Validator y CompletionProvider).
ProviderType returns string:
    'openai' | 'anthropic' | 'ollama' | 'google';

fragment ProviderModel:
    'provider' provider=ProviderType
    'model' model=STRING;

Agent:
    'agent' name=ID '{'
        //Necesario
        ProviderModel
        'profile' profile=[Profile]

        //Recomendable
        ('description' description=STRING)?
        ('stateContext' stateContext+=[Attribute] (',' stateContext+=[Attribute])*)?
        ('stateUpdate' stateUpdate+=[Attribute] (',' stateUpdate+=[Attribute])*)?

        // Opcional
        ('statusMessage' statusMessage = STRING)?
        ('temperature' temperature = FLOAT)?
        ('maxToken' maxToken = INT)?
        ('timeOut' timeOut = INT)?
        ('maxRetries' maxRetries = INT)?
        ('tools' tools+=[Tool:ID] (',' tools+=[Tool:ID])*)?
    '}';

Profile:
    'profile' name=ID 'description' profileDescription=STRING;

type Tool = PythonTool | MCPServer ;

fragment ToolBase:
    name=ID;


PythonTool:
    'pythonTool' ToolBase 'modulePath' modulePath=STRING;

MCPServer:
    'mcpServer' name=ID '{'
        'url' url=STRING
        'transport' transport=STRING
        ('apiKeyName' apiKeyName=STRING)?
        'tools' tools+=STRING (',' tools+=STRING)*
    '}';


// A partir de aquí, se define la ultima parte del metamodelo, la cual indica como se comunican entre sí los distintos agentes
// Se ha omitido CommunicationModel porque se ha descartado CommunicationParadigm
type CommunicationStructure = Layered | SharedMessagePool | Centralized | Decentralized;

fragment Agents:
    'agents' agents+=[Agent] (',' agents+=[Agent])*;

CommTransition:
    'from' (isStart?='START' | source=[CommunicationStructure])
    'to' (isEnd?='END' | target=[CommunicationStructure])
    ('when' condition=Condition)?;

ConditionType returns string:
    'equal' | 'greather' | 'lower';

Condition:
    attribute=[Attribute] operator=ConditionType value=ConditionLiteral;

ConditionLiteral:
    BoolLiteral | IntLiteral | StringLiteral;

BoolLiteral:   {infer BoolLiteral}   value=('True' | 'False');
IntLiteral:    {infer IntLiteral}    value=INT;
StringLiteral: {infer StringLiteral} value=STRING;

Layered:
    'layered' name=ID '{'
        layers+=Layer+
    '}';

Coordinator:
    'coordinator' name=ID '{'
        //Necesario
        ProviderModel
        'profile' profile=[Profile]

        // Opcional
        ('temperature' temperature = FLOAT)?
    '}';

Centralized:
    'centralized' name=ID '{'
        coordinator=Coordinator
        Agents
    '}';

SharedMessagePool:
    'shared_message_pool' name=ID '{'
        Agents
    '}';

Decentralized:
    'decentralized' name=ID '{'
        Agents
    '}';

Layer:
    'layer' name=ID 'level' level=INT
    ('next' next=[Layer])?
    'agent' agent=[Agent];

hidden terminal WS: /\s+/;
terminal ID: /[_a-zA-Z][\w_]*/;
terminal FLOAT returns number: /[0-9]+\.[0-9]+/;
terminal INT returns number: /[0-9]+/;
terminal STRING: /"(\\.|[^"\\])*"|'(\\.|[^'\\])*'/;

hidden terminal ML_COMMENT: /\/\*[\s\S]*?\*\//;
hidden terminal SL_COMMENT: /\/\/[^\n\r]*/;
