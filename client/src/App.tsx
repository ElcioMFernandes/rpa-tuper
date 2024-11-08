import axios from "axios";
import { useEffect, useState } from "react";
import List from "./components/List";
import ListItem from "./components/ListItem";

interface Task {
  task_id: string;
  task_file: string;
  next_run_time: string | null;
  trigger: string;
  args: string[];
  kwargs: {
    prefix: string;
    sufix: string;
  };
}

interface ApiResponse {
  status: string;
  message: string;
  tasks: Task[];
}

function App() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get<ApiResponse>(
          "http://127.0.0.1:8000/queue/"
        );
        setData(response.data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Erro desconhecido";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <p>Carregando...</p>;
  if (error) return <p>Erro: {error}</p>;

  return (
    <div>
      {data && (
        <div>
          <List>
            {/* Cabeçalho da lista */}
            <div className="flex items-center space-x-4 font-bold py-2 border-b">
              <span>ID da Tarefa</span>
              <span>Arquivo da Tarefa</span>
              <span>Próxima Execução</span>
              <span>Gatilho</span>
            </div>

            {/* Lista de tarefas */}

            {data.tasks.map((task) => (
              <ListItem key={task.task_id}>
                <span>{task.task_id}</span>
                <span>{task.task_file}</span>
                <span>{task.next_run_time ?? "Não definida"}</span>
                <span>{task.trigger}</span>
              </ListItem>
            ))}
          </List>
        </div>
      )}
    </div>
  );
}

export default App;
