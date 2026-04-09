import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [appState, setAppState] = useState('input'); // 'input', 'reading', 'quiz', 'results'
  const [activeTab, setActiveTab] = useState('paste');
  const [textInput, setTextInput] = useState('');
  const [fileInput, setFileInput] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Material Data
  const [materialId, setMaterialId] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [quizQuestions, setQuizQuestions] = useState([]);

  // Quiz Interaction State
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({}); // { question_id: "selected_option_string" }
  const [gradingResult, setGradingResult] = useState(null); // The result from /api/grade/

  // ------------------------------------------------------------------
  // Submit handlers for Upload / Paste
  // ------------------------------------------------------------------
  const handlePasteSubmit = async () => {
    if (!textInput.trim()) return;
    await processInput('http://127.0.0.1:8000/api/paste/', { text: textInput });
  };

  const handleFileUpload = async () => {
    if (!fileInput) return;
    const formData = new FormData();
    formData.append('file', fileInput);
    await processInput('http://127.0.0.1:8000/api/upload/', formData, {
      'Content-Type': 'multipart/form-data'
    });
  };

  const processInput = async (url, data, headers = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(url, data, { headers });
      setMaterialId(res.data.material_id);
      setSummaryData({
        summary: res.data.summary,
        explanation: res.data.explanation
      });
      setQuizQuestions(res.data.quiz);
      setAppState('reading'); // Transition to reading phase
    } catch (err) {
      setError(
        err.response?.data?.error?.file?.[0] || 
        err.response?.data?.error || 
        'An unexpected error occurred. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------------------
  // Quiz Handlers
  // ------------------------------------------------------------------
  const handleStartQuiz = () => {
    setAppState('quiz');
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOptionSelect = (questionId, option) => {
    setUserAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleSubmitQuiz = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`http://127.0.0.1:8000/api/grade/${materialId}/`, {
        answers: userAnswers
      });
      setGradingResult(res.data);
      setAppState('results');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError('Failed to submit quiz for grading. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------------------
  // Renderers
  // ------------------------------------------------------------------
  return (
    <div className="min-h-screen p-6 md:p-12 relative overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="fixed top-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-sky/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[30vw] h-[30vw] bg-mint/20 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="max-w-4xl mx-auto relative z-10">
        
        {/* Header */}
        <header className="text-center mb-12 animate-floatIn">
          <h1 
            className="text-5xl md:text-7xl font-bold mb-4 cursor-pointer" 
            onClick={() => { setAppState('input'); setTextInput(''); setFileInput(null); }}
          >
            <span className="text-gradient">MateriAI</span>
          </h1>
          {appState === 'input' && (
            <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto">
              Transform massive texts and messy PDFs into structured, intelligent study materials instantly.
            </p>
          )}
        </header>

        {/* STATE: INPUT */}
        {appState === 'input' && (
          <main className="glass-panel rounded-3xl p-6 md:p-8 mb-12 animate-floatIn" style={{ animationDelay: '0.1s' }}>
            <div className="flex gap-4 mb-8 border-b border-white/10 pb-4">
              <button onClick={() => setActiveTab('paste')} className={`pb-2 px-4 transition-all duration-300 font-semibold text-lg relative ${activeTab === 'paste' ? 'text-mint' : 'text-slate-400 hover:text-white'}`}>
                Paste Text
                {activeTab === 'paste' && <span className="absolute bottom-[-17px] left-0 w-full h-[2px] bg-mint shadow-[0_0_10px_rgba(106,216,191,0.8)] rounded-t-sm" />}
              </button>
              <button onClick={() => setActiveTab('upload')} className={`pb-2 px-4 transition-all duration-300 font-semibold text-lg relative ${activeTab === 'upload' ? 'text-sky' : 'text-slate-400 hover:text-white'}`}>
                Upload PDF
                {activeTab === 'upload' && <span className="absolute bottom-[-17px] left-0 w-full h-[2px] bg-sky shadow-[0_0_10px_rgba(90,177,255,0.8)] rounded-t-sm" />}
              </button>
            </div>

            <div className="min-h-[200px] flex flex-col justify-center">
              {activeTab === 'paste' ? (
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Paste your text here (minimum 20 characters)..."
                  className="w-full h-48 bg-black/20 border border-white/10 rounded-2xl p-5 text-white placeholder-slate-500 focus:outline-none focus:border-mint transition-colors resize-none"
                />
              ) : (
                <div className="flex items-center justify-center w-full">
                  <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-white/20 rounded-2xl cursor-pointer bg-black/10 hover:bg-black/20 hover:border-sky transition-colors">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <svg className="w-10 h-10 mb-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                      <p className="mb-2 text-sm text-slate-400 shadow-sm"><span className="font-semibold text-sky">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-slate-500">PDF or TXT (MAX. 10MB)</p>
                    </div>
                    <input id="dropzone-file" type="file" className="hidden" accept=".pdf,.txt" onChange={(e) => setFileInput(e.target.files[0])} />
                  </label>
                </div>
              )}
              {fileInput && activeTab === 'upload' && (
                 <div className="mt-4 p-3 bg-sky/10 border border-sky/30 rounded-lg text-sky text-sm flex items-center justify-between">
                   <span>Selected File: <span className="font-medium">{fileInput.name}</span></span>
                   <button onClick={() => setFileInput(null)} className="text-white hover:text-coral hover:scale-110 transition-transform">✕</button>
                 </div>
              )}
            </div>

            <div className="mt-8 flex items-center justify-between">
               {error && (
                 <p className="text-coral bg-coral/10 border border-coral/20 px-4 py-2 rounded-lg text-sm max-w-[60%]">
                   {typeof error === 'string' ? error : JSON.stringify(error)}
                 </p>
               )}
               {!error && <div/>}
               <button
                 onClick={activeTab === 'paste' ? handlePasteSubmit : handleFileUpload}
                 disabled={loading || (activeTab === 'paste' ? textInput.length < 20 : !fileInput)}
                 className={`ml-auto px-8 py-3 rounded-full font-bold text-ink shadow-[0_4px_14px_0_rgba(106,216,191,0.39)] transition-all duration-300 hover:shadow-[0_6px_20px_rgba(106,216,191,0.23)] hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none ${activeTab === 'paste' ? 'bg-mint' : 'bg-sky text-ink'}`}
               >
                 {loading ? 'Processing Material...' : 'Analyze & Prepare'}
               </button>
            </div>
          </main>
        )}

        {/* STATE: READING */}
        {appState === 'reading' && summaryData && (
          <div className="animate-floatIn space-y-8 pb-12">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-3xl font-bold text-white">Study Material</h2>
              <button 
                onClick={handleStartQuiz}
                className="bg-sky text-ink px-6 py-2 rounded-full font-bold shadow-[0_4px_14px_0_rgba(90,177,255,0.39)] hover:scale-105 transition-transform"
              >
                Ready? Take the Quiz
              </button>
            </div>

            <div className="glass-panel p-8 rounded-3xl relative overflow-hidden group">
               <div className="absolute top-0 left-0 w-2 h-full bg-mint" />
               <h3 className="text-xl font-bold mb-4">⚡ Executive Summary</h3>
               <p className="text-slate-300 leading-relaxed text-lg">{summaryData.summary}</p>
            </div>

            <div className="glass-panel p-8 rounded-3xl relative overflow-hidden">
               <div className="absolute top-0 left-0 w-2 h-full bg-sky" />
               <h3 className="text-xl font-bold mb-4">📖 Detailed Explanation</h3>
               <div className="text-slate-300 leading-relaxed space-y-4">
                 {summaryData.explanation.split('\n').map((para, i) => (
                   <p key={i}>{para}</p>
                 ))}
               </div>
            </div>
            
            <div className="flex justify-center mt-10">
              <button 
                onClick={handleStartQuiz}
                className="bg-indigo-500 text-white px-10 py-4 rounded-full font-bold text-lg shadow-[0_4px_20px_0_rgba(99,102,241,0.4)] hover:scale-105 transition-all"
              >
                Begin Knowledge Check
              </button>
            </div>
          </div>
        )}

        {/* STATE: QUIZ (Interactive, 1-by-1) */}
        {appState === 'quiz' && quizQuestions.length > 0 && (
          <div className="animate-floatIn pb-12">
            
            {/* Progress Bar */}
            <div className="mb-8">
              <div className="flex justify-between text-slate-400 font-semibold mb-2">
                <span>Question {currentQuestionIndex + 1} of {quizQuestions.length}</span>
                <span>{Math.round(((currentQuestionIndex) / quizQuestions.length) * 100)}% Completed</span>
              </div>
              <div className="w-full bg-black/30 rounded-full h-2.5">
                <div 
                  className="bg-sky h-2.5 rounded-full transition-all duration-500 ease-out" 
                  style={{ width: `${((currentQuestionIndex + 1) / quizQuestions.length) * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="glass-panel p-8 rounded-3xl mb-8 border-t-4 border-t-sky shadow-xl">
              <h2 className="text-2xl font-semibold text-white mb-8 leading-relaxed">
                {quizQuestions[currentQuestionIndex].question}
              </h2>

              <div className="space-y-4">
                {quizQuestions[currentQuestionIndex].options.map((opt, i) => {
                  const qId = quizQuestions[currentQuestionIndex].id;
                  const isSelected = userAnswers[qId] === opt;
                  return (
                    <div 
                      key={i}
                      onClick={() => handleOptionSelect(qId, opt)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 flex items-center gap-4 group
                        ${isSelected ? 'bg-sky/10 border-sky shadow-[0_0_15px_rgba(90,177,255,0.2)]' : 'border-white/10 bg-black/20 hover:border-white/30 hover:bg-white/5'}
                      `}
                    >
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                        ${isSelected ? 'border-sky' : 'border-slate-500 group-hover:border-slate-400'}
                      `}>
                        {isSelected && <div className="w-3 h-3 bg-sky rounded-full" />}
                      </div>
                      <span className={`text-lg ${isSelected ? 'text-white' : 'text-slate-300'}`}>{opt}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Nav & Submit */}
            <div className="flex items-center justify-between">
              <button 
                onClick={handlePrevQuestion}
                disabled={currentQuestionIndex === 0}
                className="px-6 py-2 text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
              >
                ← Previous
              </button>

              {currentQuestionIndex === quizQuestions.length - 1 ? (
                <button 
                  onClick={handleSubmitQuiz}
                  disabled={loading}
                  className="bg-mint text-ink px-8 py-3 rounded-full font-bold shadow-[0_4px_14px_0_rgba(106,216,191,0.39)] hover:scale-105 transition-transform disabled:opacity-70"
                >
                  {loading ? 'Grading...' : 'Submit Exam'}
                </button>
              ) : (
                <button 
                  onClick={handleNextQuestion}
                  className="bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-full font-bold transition-all"
                >
                  Next →
                </button>
              )}
            </div>

            {error && <p className="text-coral mt-6 text-center">{error}</p>}
          </div>
        )}

        {/* STATE: RESULTS */}
        {appState === 'results' && gradingResult && (
          <div className="animate-floatIn pb-12">
            {/* Score Banner */}
            <div className="glass-panel p-8 rounded-3xl mb-12 text-center relative overflow-hidden">
               <div className={`absolute top-0 left-0 w-full h-2 ${gradingResult.score / gradingResult.total >= 0.7 ? 'bg-mint' : 'bg-coral'}`} />
               <h2 className="text-4xl font-bold mb-2">Quiz Complete!</h2>
               <div className="flex items-baseline justify-center gap-2 mt-4">
                 <span className="text-7xl font-display font-black text-white">{gradingResult.score}</span>
                 <span className="text-3xl text-slate-400">/ {gradingResult.total}</span>
               </div>
               <p className="mt-4 text-slate-400 text-lg">
                 {gradingResult.score / gradingResult.total >= 0.8 ? 'Excellent work! You mastered this material.' : 
                  gradingResult.score / gradingResult.total >= 0.5 ? 'Good job, but there is room for review.' : 
                  'Keep studying! Review the material and try again.'}
               </p>
            </div>

            {/* Detailed Review */}
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <span className="text-sky">📝</span> Detailed Review
            </h3>
            
            <div className="space-y-6">
              {quizQuestions.map((q, i) => {
                const res = gradingResult.results[q.id.toString()];
                const isCorrect = res?.correct;
                const userAnswer = res?.user_answer;
                const correctAnswer = res?.correct_answer;

                return (
                  <div key={q.id} className="glass-panel p-6 rounded-2xl border-l-4" style={{ borderLeftColor: isCorrect ? '#6ad8bf' : '#ff6b5e' }}>
                    <p className="font-semibold text-lg text-white mb-4">
                      {i + 1}. {q.question}
                    </p>
                    
                    <div className="space-y-3">
                      {q.options.map((opt, j) => {
                        let rowClass = "p-3 rounded-xl border border-white/5 bg-black/20 text-slate-400";
                        let icon = "";

                        // If this option is the correct answer
                        if (opt === correctAnswer) {
                          rowClass = "p-3 rounded-xl border border-mint/50 bg-mint/10 text-mint font-medium shadow-[0_0_10px_rgba(106,216,191,0.1)]";
                          icon = "✓";
                        }
                        // If this option is what the user selected, and it was WRONG
                        else if (opt === userAnswer && !isCorrect) {
                          rowClass = "p-3 rounded-xl border border-coral/50 bg-coral/10 text-coral font-medium";
                          icon = "✗";
                        }

                        return (
                          <div key={j} className={`flex items-center justify-between ${rowClass}`}>
                            <span>{opt}</span>
                            {icon && <span className="text-lg font-bold">{icon}</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-12 text-center">
              <button 
                onClick={() => { setAppState('input'); setTextInput(''); setFileInput(null); }}
                className="bg-transparent border border-white/20 text-white px-8 py-3 rounded-full font-bold hover:bg-white/10 transition-colors"
              >
                Analyze Another Document
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default App;
