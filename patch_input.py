import re

with open("frontend/src/app/page.tsx", "r") as f:
    content = f.read()

old_input_section = """            <div className="p-4 bg-white dark:bg-slate-950 border-t shadow-[0_-4px_10px_-5px_rgba(0,0,0,0.05)] shrink-0">
              <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2 relative">
                <Input 
                  value={input} 
                  onChange={e => setInput(e.target.value)} 
                  placeholder="Ask an analytical question..." 
                  className="pr-12 rounded-full bg-slate-100 dark:bg-slate-900 border-transparent focus-visible:ring-1 focus-visible:ring-[#2053a4] h-12"
                  disabled={loading}
                />
                <Button 
                  type="submit" 
                  size="icon" 
                  disabled={!input.trim() || loading}
                  className="absolute right-1.5 top-1.5 w-9 h-9 rounded-full bg-[#2053a4] hover:bg-[#1d3761] text-white shadow-sm transition-all"
                >
                  <Send size={15} />
                </Button>
              </form>
            </div>"""

new_input_section = """            <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent dark:from-slate-950 dark:via-slate-950 pt-8 shrink-0 relative z-10">
              <div className="max-w-4xl mx-auto relative rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus-within:ring-2 focus-within:ring-[#2053a4]/20 focus-within:border-[#2053a4] transition-all">
                <textarea 
                  value={input} 
                  onChange={e => {
                    setInput(e.target.value);
                    // Simple auto-resize logic
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask an analytical question..." 
                  className="w-full min-h-[60px] max-h-[200px] resize-none bg-transparent py-4 pl-5 pr-14 text-[15px] placeholder:text-slate-400 focus:outline-none dark:text-slate-200"
                  disabled={loading}
                  rows={1}
                />
                <Button 
                  onClick={(e) => { e.preventDefault(); handleSend(); }}
                  size="icon" 
                  disabled={!input.trim() || loading}
                  className="absolute right-2.5 bottom-2.5 w-10 h-10 rounded-xl bg-[#2053a4] hover:bg-[#1d3761] text-white shadow-sm transition-all disabled:opacity-50 disabled:bg-slate-200 disabled:text-slate-400 dark:disabled:bg-slate-800"
                >
                  <Send size={16} className={input.trim() ? "translate-x-0.5 -translate-y-0.5" : ""} />
                </Button>
              </div>
              <p className="text-center text-xs text-slate-400 mt-3 font-medium">ZATCA Remedy AI can make mistakes. Check important info.</p>
            </div>"""

if old_input_section in content:
    content = content.replace(old_input_section, new_input_section)
    with open("frontend/src/app/page.tsx", "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Could not find the old input section. Checking what is actually there:")
    import sys
    print(content[-1500:])
