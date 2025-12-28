//This will set visual hierarchy and makes the app feel intentional
export default function ChatHeader({ onReset }) {
  return (
    <div className="chat-header">
      <h2>AI Cloud Assistant - Powered by AWS Bedrock</h2>
      <button className="reset-btn" onClick={onReset}>
        RESET
      </button>
    </div>
  );
}
