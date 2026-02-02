'use client';

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
    isLoading?: boolean;
}

export default function ConfirmModal({
    isOpen,
    title,
    message,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    onConfirm,
    onCancel,
    isLoading = false,
}: ConfirmModalProps) {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2 className="modal-title">{title}</h2>
                    <button className="modal-close" onClick={onCancel}>
                        ✕
                    </button>
                </div>
                <div className="modal-body">
                    <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{message}</p>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onCancel} disabled={isLoading}>
                        {cancelLabel}
                    </button>
                    <button className="btn btn-success" onClick={onConfirm} disabled={isLoading}>
                        {isLoading ? (
                            <>
                                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                Processing...
                            </>
                        ) : (
                            confirmLabel
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
