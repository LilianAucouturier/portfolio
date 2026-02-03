export default function CoachPage() {
    return (
        <div className="p-6">
            <h1 className="text-3xl font-bold mb-4">Coach IA</h1>
            <p className="text-zinc-400 mb-8">
                Posez vos questions à votre coach personnel.
            </p>

            {/* Placeholder chat interface */}
            <div className="bg-zinc-900 rounded-xl p-6 min-h-[400px] flex items-center justify-center">
                <p className="text-zinc-500 text-center">
                    Interface de chat avec Gemini AI<br />
                    <span className="text-sm">À implémenter</span>
                </p>
            </div>
        </div>
    );
}
