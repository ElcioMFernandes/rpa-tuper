import React from "react";

// Define as props para o List
interface ListProps {
  children: React.ReactNode;
}

const List: React.FC<ListProps> = ({ children }) => {
  return <ul className="border border-gray-300 rounded">{children}</ul>;
};

export default List;
