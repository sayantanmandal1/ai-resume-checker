import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export default function TestPDF() {
  const generatePDF = () => {
    const doc = new jsPDF();

    doc.setFontSize(16);
    doc.text('Test Candidate Report', 14, 20);

    // Pass the doc instance as the first argument
    autoTable(doc, {
      startY: 30,
      head: [['Category', 'Score']],
      body: [
        ['Skill Match', '85.5%'],
        ['Experience', '70.3%'],
      ],
      theme: 'striped',
    });

    doc.save('test_report.pdf');
  };

  return <button onClick={generatePDF}>Generate PDF</button>;
}
