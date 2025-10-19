import { useState } from 'react';

export type MessageStatus = 'thinking' | 'routing' | 'writing' | 'complete' | 'error';
export type MessageType = 'text' | 'image';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status?: MessageStatus;
  statusText?: string;
  imageUrl?: string;
}

interface AdkEvent {

  content?: {

    parts?: Array<{

      text?: string;

      functionCall?: {

        name: string;

        args: { [key: string]: any };

      }

    }>;

  };

  author?: string;

  error?: string;

  finishReason?: string;

}



const formatAgentName = (name: string = "") => {

  return name.replace(/specialist_/g, '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

}



export const useChat = () => {

  const [messages, setMessages] = useState<Message[]>([]);

  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<Error | null>(null);



  const sendMessage = async (userInput: string) => {

    if (!userInput.trim()) return;



    setIsLoading(true);

    setError(null);



    const newUserMessage: Message = {

      id: Date.now().toString(),

      role: 'user',

      content: userInput,

      type: 'text',

    };

    

    const assistantMessageId = (Date.now() + 1).toString();

    setMessages((prevMessages) => [

      ...prevMessages,

      newUserMessage,

      {

        id: assistantMessageId,

        role: 'assistant',

        content: '',

        status: 'thinking',

        statusText: 'Thinking...',

        type: 'text',

      }

    ]);



    try {

      const sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2)}`;

      const appName = 'sahabat';

      const userId = 'frontend-user';



      await fetch(`http://localhost:8000/session/${appName}/users/${userId}/sessions/${sessionId}`, {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify({}) 

      });



      const payload = {

        app_name: appName,

        user_id: userId,

        session_id: sessionId,

        new_message: {

          parts: [{ text: userInput }],

        },

        streaming: true,

      };



      const response = await fetch('http://localhost:8000/chat', {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify(payload),

      });



      if (!response.body) throw new Error('Response body is null');



      const reader = response.body.getReader();

      const decoder = new TextDecoder();

      let buffer = '';

      let firstOrchestratorEvent = true;



      while (true) {

        const { done, value } = await reader.read();

        

        if (done) {

          setMessages((prev) => prev.map(m => m.id === assistantMessageId ? {...m, status: 'complete'} : m));

          break;

        }



        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');

        buffer = lines.pop() || '';



        for (const line of lines) {

          if (line.startsWith('data:')) {

            try {

              const jsonString = line.substring(5);

              if (jsonString.trim()) {

                const event: AdkEvent = JSON.parse(jsonString);



                if (event.error) throw new Error(`Backend error: ${event.error}`);



                if (event.author === 'sahabat_orchestrator') {

                  if (firstOrchestratorEvent) {

                    setMessages((prev) => prev.map(m => m.id === assistantMessageId ? {...m, status: 'routing', statusText: 'Talking to the Sahabat Router...'} : m));

                    firstOrchestratorEvent = false;

                  }

                  

                  const functionCall = event.content?.parts?.[0]?.functionCall;

                  if (functionCall?.name === 'transfer_to_agent') {

                    const agentName = formatAgentName(functionCall.args.agent_name);

                    setMessages((prev) => prev.map(m => m.id === assistantMessageId ? {...m, status: 'routing', statusText: `Routing to the ${agentName} Agent...`} : m));

                  }

                                } else if (event.author === 'specialist_text') {

                                  const textChunk = event.content?.parts?.[0]?.text;

                                  if (textChunk) {

                                    setMessages((prev) =>

                                      prev.map((msg) =>

                                        msg.id === assistantMessageId

                                          ? { ...msg, status: 'writing', content: msg.content + textChunk }

                                          : msg

                                      )

                                    );

                                  }

                                } else if (event.author === 'specialist_image') {

                                  const jsonChunk = event.content?.parts?.[0]?.text;

                                  if (jsonChunk) {

                                    try {

                                      // The final response from the image agent is a single JSON object.

                                      const imageData = JSON.parse(jsonChunk);

                                      setMessages((prev) =>

                                        prev.map((msg) =>

                                          msg.id === assistantMessageId

                                            ? { 

                                                ...msg, 

                                                status: 'complete', 

                                                content: imageData.text, 

                                                imageUrl: imageData.imageUrl 

                                              }

                                            : msg

                                        )

                                      );

                                    } catch (e) {

                                      // Handle cases where the JSON is streamed in chunks

                                      console.log("Parsing partial JSON...", jsonChunk);

                                    }

                                  }

                                }

              }

            } catch (e) {

              console.error("Failed to parse SSE chunk:", line, e);

            }

          }


        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(new Error(errorMessage));
       setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, content: `Error: ${errorMessage}`, status: 'error' } : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, error, sendMessage };
};
