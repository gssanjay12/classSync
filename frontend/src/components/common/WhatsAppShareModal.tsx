import React, { useState } from 'react';
import { X, Copy, Check, MessageSquareShare, ExternalLink } from 'lucide-react';
import { useToast } from '../../contexts/ToastContext';

interface WhatsAppShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  classNameTitle: string;
  question: string;
  shareUrl: string;
  whatsappShareUrl: string;
}

export const WhatsAppShareModal: React.FC<WhatsAppShareModalProps> = ({
  isOpen,
  onClose,
  classNameTitle,
  question,
  shareUrl,
  whatsappShareUrl,
}) => {
  const [copied, setCopied] = useState(false);
  const { success } = useToast();

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    success('Poll link copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const previewMessage = `*${classNameTitle} Poll*\n\n${question}\n\n👉 Submit your response here:\n${shareUrl}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <MessageSquareShare className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-lg">Share Poll to WhatsApp</h3>
              <p className="text-xs text-slate-500">Distribution via WhatsApp, tracking via ClassPoll</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              WhatsApp Message Preview
            </label>
            <div className="p-4 rounded-xl bg-emerald-950/5 border border-emerald-500/20 text-slate-800 text-sm font-mono whitespace-pre-wrap leading-relaxed">
              {previewMessage}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Direct Poll URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={shareUrl}
                className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 select-all focus:outline-hidden"
              />
              <button
                onClick={handleCopy}
                className={`inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  copied
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 active:scale-95'
                }`}
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-100 bg-slate-50/50">
          <button
            onClick={onClose}
            className="px-4 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
          >
            Done
          </button>
          <a
            href={whatsappShareUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#25D366] hover:bg-[#20bd5a] text-white text-sm font-semibold rounded-xl shadow-sm transition-all transform active:scale-95"
          >
            <MessageSquareShare className="w-4 h-4" />
            <span>Open in WhatsApp</span>
            <ExternalLink className="w-3.5 h-3.5 opacity-75" />
          </a>
        </div>
      </div>
    </div>
  );
};
