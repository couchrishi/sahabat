import { useState, useRef, useEffect } from "react";
import { Search, Sparkles, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { useChat, Message } from "@/hooks/useChat";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

const Index = () => {
  const [query, setQuery] = useState("");
  const { messages, isLoading, sendMessage } = useChat();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    sendMessage(query);
    setQuery("");
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar
          conversations={[]}
          activeConversationId={null}
          onNewConversation={() => {}}
          onSelectConversation={() => {}}
          onDeleteConversation={() => {}}
        />
        
        <main className="flex-1 flex flex-col h-screen">
          <header className="border-b border-border bg-card/50 backdrop-blur-sm">
            <div className="container mx-auto px-4 py-4 flex items-center gap-4">
              <SidebarTrigger className="lg:hidden" />
              <div className="flex items-center gap-2">
                <Sparkles className="h-6 w-6 text-primary" />
                <h1 className="text-xl font-semibold text-foreground">Sahabat AI</h1>
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-auto" ref={scrollAreaRef}>
            <div className="container mx-auto px-4 py-8">
              <div className="mx-auto max-w-3xl">
                {messages.length === 0 ? (
                  <div className="text-center">
                    <h2 className="mb-4 text-4xl font-bold tracking-tight text-foreground md:text-5xl">
                      Ask anything
                    </h2>
                    <p className="text-lg text-muted-foreground">
                      Get instant, intelligent answers powered by AI
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {messages.map((msg) => {
                      if (msg.role === 'assistant' && (msg.status === 'thinking' || msg.status === 'routing')) {
                        // Show status text inside the bubble while thinking or routing
                        return (
                         <div key={msg.id} className="flex items-start gap-4">
                           <div className="max-w-lg rounded-lg p-4 bg-muted">
                             <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="h-2 w-2 animate-pulse rounded-full bg-foreground" />
                                <span className="text-sm italic">
                                 {msg.statusText || 'Processing...'}
                                </span>
                             </div>
                           </div>
                         </div>
                        );
                      }

                      return (
                        <div
                          key={msg.id}
                          className={cn(
                            "flex items-start gap-4",
                            msg.role === "user" ? "justify-end" : ""
                          )}
                        >
                          <div
                            className={cn(
                              "max-w-lg rounded-lg p-4",
                              msg.role === "user"
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted"
                            )}
                          >
                            <article className="prose dark:prose-invert">
                              <div>
                                {msg.content}
                                {msg.status === 'writing' && !msg.imageUrl && (
                                  <span className="inline-block h-4 w-1 animate-pulse bg-foreground" />
                                )}
                              </div>
                              {msg.imageUrl && (
                                <img src={msg.imageUrl} alt="Generated content" className="mt-4 rounded-lg" />
                              )}
                            </article>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="border-t border-border bg-card/50 backdrop-blur-sm">
            <div className="container mx-auto px-4 py-4">
              <div className="mx-auto max-w-3xl">
                <form onSubmit={handleSearch}>
                  <div className="relative">
                    <Input
                      type="text"
                      placeholder="Ask anything..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      disabled={isLoading}
                      className="h-14 pr-16 text-base"
                    />
                    <Button
                      type="submit"
                      size="icon"
                      disabled={!query.trim() || isLoading}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                    >
                      <Send className="h-5 w-5" />
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
};

export default Index;