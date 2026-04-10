grammar MultiAgentDsl

entry LLMMultiAgentSystem:
    '{'
        envirement=Environment
        profiles+=Profile*
        tools+=(PythonTool | MCPTool | EndPointTool)*
        agents+=Agent*
        communicationStructures+=(Layered | SharedMessagePool | Centralized | Decentralized)*
    '}';

// Toda esta sección define la parte del entorno en que se encuentra el MAAS.
// GameRule: Debe revisarse

AttributeType returns string:
    'int' | 'string' | 'boolean';

Environment:
    'environment' name = ID '{'
        gamerules+=GameRule*
        attributes+=Attribute*
        messages=(Trim | Mix | None | Summarize)
    '}';

GameRule:
    'gamerule' id = ID 'description' description = STRING;

Attribute:
    'attribute' name = ID 'type' type = AttributeType 'description' description = STRING;

type Message = Trim | Mix | None | Summarize;

Trim:
    'trim' 'maxToken' maxToken = INT;

Mix:
    'mix' 'maxToken' maxToken = INT;

None:
    {infer None} 'none';

Summarize:
    'summarize' 'maxToken' maxToken = INT;

// A partir de ahora, se define todo lo relacionado con los agentes individuales:
ModelType returns string:
    'gpt' | 'claude' | 'ollama';

Agent:
    'agent' name=ID '{'
        //Necesario
        'model' model=ModelType
        'profile' profile=[Profile]

        //Recomendable
        ('stateContext' stateContext+=[Attribute]*)?
        ('stateUpdate' stateUpdate+=[Attribute]*)?

        // Opcional
        ('temperature' temperature = INT)?
        ('maxToken' maxToken = INT)?
        ('timeOut' timeOut = INT)?
        ('maxRetries' maxRetries = INT)?
        ('tools' tools+=[Tool:ID] (',' tools+=[Tool:ID])*)?
    '}';

Profile:
    'profile' name=ID 'description' profileDescription=STRING;

type Tool = PythonTool | MCPTool | EndPointTool;

fragment ToolBase:
    name=ID 
    'description' description=STRING
    ('params' '{' param+=Param* '}')?;

Param:
    name=ID 'type' type=AttributeType;

PythonTool:
    'pythonTool' ToolBase 'modulePath' modulePath=STRING;

MCPTool:
    'mcpTool' ToolBase'{'
        'serverUrl' serverUrl=STRING
        'transport' transport=STRING
        ('key' key=STRING)?
    '}';

MethodType returns string:
    'GET' | 'POST' | 'PUT' | 'DELETE';

EndPointTool:
    'endpointTsool' ToolBase'{'
        'url' url=STRING
        'method' method=MethodType
    '}';

// A partir de aquí, se define la ultima parte del metamodelo, la cual indica como se comunican entre sí los distintos agentes
// Se ha omitido CommunicationModel porque se ha descartado CommunicationParadigm 
type CommunicationStructure = Layered | SharedMessagePool | Centralized | Decentralized;

fragment NextCommStructure:
    ('next' next=[CommunicationStructure])?;

Layered:
    'layered' name=ID '{'
        layers+=Layer+
    '}' NextCommStructure;

Centralized:
    'centralized' name=ID 'coordinator' coordinator=[Agent] NextCommStructure;

SharedMessagePool:
    {infer SharedMessagePool} 'shared_message_pool' NextCommStructure;

Decentralized:
    {infer Decentralized} 'decentralized' NextCommStructure;

Layer:
    'layer' name=ID 'level' level=INT
    ('next' next=[Layer])?
    'agent' agent=[Agent];

hidden terminal WS: /\s+/;
terminal ID: /[_a-zA-Z][\w_]*/;
terminal INT returns number: /[0-9]+/;
terminal STRING: /"(\\.|[^"\\])*"|'(\\.|[^'\\])*'/;

hidden terminal ML_COMMENT: /\/\*[\s\S]*?\*\//;
hidden terminal SL_COMMENT: /\/\/[^\n\r]*/;
