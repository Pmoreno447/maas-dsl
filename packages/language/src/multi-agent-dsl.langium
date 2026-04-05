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
    'attribute' name = ID 'type' type = AttributeType;

type Message = Trim | Mix | None | Summarize;

Trim:
    'trim' 'trigger' trigger=INT;

Mix:
    'mix' 'trigger' trigger=INT;

None:
    {infer None} 'none';

Summarize:
    {infer Summarize} 'summarize';

// A partir de ahora, se define todo lo relacionado con los agentes individuales:
ModelType returns string:
    'gpt' | 'claude' | 'ollama';

Agent:
    'agent' name=ID '{'
        'model' model=ModelType
        'profile' profile=[Profile]
    '}';

Profile:
    'profile' name=ID 'description' profileDescription=STRING;

type Tool = PythonTool | MCPTool | EndPointTool;

fragment ToolBase:
    name=ID 'description' description=STRING
    ('params' '{' param+=Param* '}')?;

Param:
    name=ID 'type' type=AttributeType;

PythonTool:
    'pythonTool' ToolBase '{'
        'modulePath' modulePath=STRING
        'functionName' functionName=STRING
    '}';

MCPTool:
    'mcpTool' ToolBase'{'
        'serverUrl' serverUrl=STRING
        'serverName' serverName=STRING
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

Layered:
    'layered' name=ID '{'
        layers+=Layer+
    '}';

Layer:
    'layer' name=ID 'level' level=INT
    ('next' next=[Layer])?
    'agent' agent=[Agent];

Centralized:
    'centralized' name=ID 'coordinator' coordinator=[Agent];

SharedMessagePool:
    {infer SharedMessagePool} 'shared_message_pool';

Decentralized:
    {infer Decentralized} 'decentralized';


hidden terminal WS: /\s+/;
terminal ID: /[_a-zA-Z][\w_]*/;
terminal INT returns number: /[0-9]+/;
terminal STRING: /"(\\.|[^"\\])*"|'(\\.|[^'\\])*'/;

hidden terminal ML_COMMENT: /\/\*[\s\S]*?\*\//;
hidden terminal SL_COMMENT: /\/\/[^\n\r]*/;
