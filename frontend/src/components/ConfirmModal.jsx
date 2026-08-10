import { X, AlertTriangle } from 'lucide-react';
import './ConfirmModal.css';

export default function ConfirmModal({ 
  title = 'Confirm Action', 
  message = 'Are you sure you want to proceed?', 
  confirmText = 'Confirm', 
  cancelText = 'Cancel', 
  onConfirm, 
  onCancel, 
  isDestructive = true 
}) {
  return (
    <div className="confirm-modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onCancel(); }}>
      <div className="confirm-modal-card">
        <div className="confirm-modal-header">
          <div className="confirm-modal-title-group">
            {isDestructive && <AlertTriangle size={20} className="confirm-modal-icon-danger" />}
            <h2>{title}</h2>
          </div>
          <button className="confirm-modal-close" onClick={onCancel} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        
        <div className="confirm-modal-body">
          <p>{message}</p>
        </div>

        <div className="confirm-modal-actions">
          <button 
            className="confirm-modal-btn confirm-modal-btn--cancel" 
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button 
            className={`confirm-modal-btn ${isDestructive ? 'confirm-modal-btn--danger' : 'confirm-modal-btn--primary'}`} 
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
