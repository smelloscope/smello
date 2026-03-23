import Layout from "./components/Layout";
import SplitView from "./pages/SplitView";
import HotkeyHelpDialog from "./hotkeys/HotkeyHelpDialog";
import CopySnackbar from "./components/CopySnackbar";

export default function App() {
  return (
    <Layout>
      <SplitView />
      <HotkeyHelpDialog />
      <CopySnackbar />
    </Layout>
  );
}
